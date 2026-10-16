"""Opt-in live regression: isolated outputs, installed engines, per-file ffprobe."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

CASES = {
    'instagram_video_first': 'https://www.instagram.com/p/CYBuDSRsml1/',
    'instagram_image_first': 'https://www.instagram.com/p/DWRPR8xDQJt/',
    'x_multiple': 'https://x.com/JocelynVLaidlaw/status/1600649710662213632',
    'x_video_first': 'https://x.com/KingJames/status/1576321110919913472',
    'x_image_first': 'https://x.com/crly___/status/1582642358645977090',
    'x_gif': 'https://x.com/RAC/status/1954993021730410510',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    parser.add_argument('--case', choices=CASES, action='append')
    parser.add_argument('--normalize', action='store_true')
    parser.add_argument('--format', default='mp4', choices=['mp4', 'mkv', 'webm', 'mp3', 'wav', 'm4a'])
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
    import utils.app_paths
    utils.app_paths.get_user_data_path = lambda: str(output)
    import utils.bin.storage
    binaries = Path(os.environ['APPDATA']) / 'YTDownloader' / 'bin'
    utils.bin.storage.get_bin_path = lambda: str(binaries)
    from core.download.runner import download_video_with_result
    from utils.settings_store import default_settings

    report = {'version': subprocess.check_output(
        [str(binaries / 'yt-dlp.exe'), '--version'], text=True, encoding='utf-8').strip(), 'cases': []}
    for name in args.case or CASES:
        settings = default_settings()
        settings.update(normalize_audio=args.normalize, format=args.format)
        folder = output / name
        folder.mkdir()
        settings['download_folder'] = str(folder)
        started = time.monotonic()
        result = download_video_with_result(
            CASES[name], settings, lambda _: None,
            stop_check=lambda: time.monotonic() - started > 240,
        )
        row = {'name': name, 'success': result.success, 'message': result.message,
               'settings': dict(settings),
               'items': result.items, 'seconds': round(time.monotonic() - started, 2), 'probes': []}
        for path in result.final_paths:
            probe = subprocess.run(
                [str(binaries / 'ffprobe.exe'), '-v', 'error', '-show_entries',
                 'format=duration:stream=codec_type,codec_name,width,height', '-of', 'json', path],
                capture_output=True, text=True, encoding='utf-8', timeout=30,
            )
            row['probes'].append({'file': path, 'exit_code': probe.returncode,
                                  'info': json.loads(probe.stdout) if probe.returncode == 0 else probe.stderr})
        report['cases'].append(row)
        (output / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(row, ensure_ascii=True), flush=True)


if __name__ == '__main__':
    main()
