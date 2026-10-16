"""Measure local batch bookkeeping only; no network or media encoding."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
    import utils.app_paths
    utils.app_paths.get_user_data_path = lambda: str(output.resolve())
    from core.download import media_batch
    from core.download.media_discovery import MediaEntry
    from core.download.result import DownloadResult

    rows = []
    for count in (1, 10, 100):
        with tempfile.TemporaryDirectory(dir=output) as directory:
            root = Path(directory).resolve()
            workspace = root / '.ytdl_temp' / ('a' * 32)
            workspace.mkdir(parents=True)
            entries = [MediaEntry(str(i), {'id': str(i), 'title': 'video'}, 'media') for i in range(count)]
            events = []

            def execute(_url, options, _progress, **kwargs):
                info = json.loads(Path(options['_media_info_filename']).read_text(encoding='utf-8'))
                kwargs['metadata_hook']({'download_streams': [{'id': 'v', 'kind': 'video', 'size': 1}]})
                path = root / (info['id'] + '.mp4')
                path.write_bytes(b'fixture')
                return DownloadResult(True, 'ok', str(path))

            with patch.object(media_batch, 'discover_media', return_value=({'id': 'post'}, entries)), \
                 patch.object(media_batch, 'save_manifest', wraps=media_batch.save_manifest) as save:
                start = time.perf_counter()
                result = media_batch.run_media_batch(None, 'https://example.org/post', {}, str(workspace),
                    str(root), lambda _: None, events.append, None, False, execute)
                elapsed = time.perf_counter() - start
            assert result.success and len(result.final_paths) == count
            rows.append({'videos': count, 'journal_writes': save.call_count,
                         'full_metadata_events': sum('media_items' in event for event in events),
                         'total_metadata_events': len(events), 'seconds': elapsed})
    (output / 'results.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
