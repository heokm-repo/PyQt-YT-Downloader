import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from constants import MSG_PAUSED_BY_USER
from core.download import media_batch, runner
from core.download.media_discovery import MediaEntry
from core.download.media_manifest import load_manifest, manifest_signature
from core.download.result import DownloadResult


@pytest.fixture
def batch(tmp_path, monkeypatch):
    workspace = tmp_path / '.ytdl_temp' / ('a' * 32)
    workspace.mkdir(parents=True)
    entries = [MediaEntry('site:' + name, {'id': name, 'title': 'same', 'extractor': 'site'}, kind)
               for name, kind in [('a', 'media'), ('photo', 'image'), ('b', 'media')]]
    parent = {'id': 'post', 'title': 'Post', 'extractor': 'site'}
    monkeypatch.setattr(media_batch, 'discover_media', lambda *args: (parent, entries))
    settings = {'format': 'mp4'}
    calls, snapshots = [], []

    def save(url, options, progress, **kwargs):
        info_path = Path(options['_media_info_filename'])
        info = json.loads(info_path.read_text(encoding='utf-8'))
        calls.append(info['id'])
        assert info_path.is_relative_to(workspace)
        kwargs['metadata_hook']({'id': info['id'], 'title': 'child', 'download_streams': ['video']})
        name = options['output_template'].replace('%(title)s', info['title']).replace('%(ext)s', 'mp4')
        path = tmp_path / name
        path.write_bytes(info['id'].encode() * 10)
        return DownloadResult(True, 'ok', str(path))

    def run(callback=save, resume=False, stop=None):
        return media_batch.run_media_batch(Mock(), 'https://example.org/post', settings, str(workspace),
                                          str(tmp_path), lambda _: None, snapshots.append, stop, resume, callback)

    return run, save, entries, calls, snapshots, workspace, settings


def test_saves_all_same_title_videos_skips_photo_and_cleans_only_own_workspace(batch):
    run, _, _, calls, snapshots, workspace, _ = batch
    sibling = workspace.parent / ('b' * 32)
    sibling.mkdir()
    sentinel = sibling / 'keep.part'
    sentinel.write_bytes(b'other task')
    result = run()
    assert result.success and calls == ['a', 'b']
    assert len(set(result.final_paths)) == 2
    assert [Path(p).read_bytes() for p in result.final_paths] == [b'a' * 10, b'b' * 10]
    assert [item['state'] for item in result.items] == ['completed', 'skipped', 'completed']
    assert all(s['id'] == 'post' and s['title'] == 'Post' for s in snapshots if 'media_items' in s)
    assert not workspace.exists() and sentinel.read_bytes() == b'other task'


@pytest.mark.parametrize('failure', ['network', 'pause', 'exception'])
def test_partial_success_and_resume_only_unfinished(batch, failure):
    run, save, _, calls, _, workspace, settings = batch
    count = 0

    def fail_second(*args, **kwargs):
        nonlocal count
        count += 1
        if count == 2:
            if failure == 'exception':
                raise RuntimeError('conversion failed')
            return DownloadResult(False, MSG_PAUSED_BY_USER if failure == 'pause' else 'HTTP 403')
        return save(*args, **kwargs)

    first = run(fail_second)
    assert not first.success and len(first.final_paths) == 1
    path = Path(first.final_path)
    stat = path.stat()
    saved = load_manifest(workspace, manifest_signature('https://example.org/post', settings))
    assert saved['site:a']['state'] == 'completed' and saved['site:b']['state'] == 'failed'
    assert not list(workspace.rglob('.entry_info.json'))
    second = run(resume=True)
    assert second.success and calls == ['a', 'b']
    assert path.stat().st_mtime_ns == stat.st_mtime_ns
    assert path.read_bytes() == b'a' * 10


def test_missing_completed_output_is_downloaded_again(batch):
    run, save, _, calls, _, _, _ = batch
    first = run(lambda *a, **kw: save(*a, **kw) if not calls else DownloadResult(False, 'fail'))
    Path(first.final_path).unlink()
    assert run(resume=True).success
    assert calls == ['a', 'a', 'b']


def test_unknown_formats_prevent_false_complete_but_keep_valid_video(batch):
    run, _, entries, calls, _, workspace, _ = batch
    entries[2].kind = 'unknown'
    result = run()
    assert not result.success and calls == ['a'] and len(result.final_paths) == 1
    assert result.items[-1]['state'] == 'failed' and workspace.exists()


def test_photos_only_have_no_downloads(batch):
    run, _, entries, calls, _, _, _ = batch
    for e in entries:
        e.kind = 'image'
    result = run()
    assert not result.success and not result.final_paths and not calls
    assert all(item['state'] == 'skipped' for item in result.items)


def test_stream_metadata_does_not_write_full_journal(batch, monkeypatch):
    run, _, _, _, snapshots, _, _ = batch
    save = Mock(wraps=media_batch.save_manifest)
    monkeypatch.setattr(media_batch, 'save_manifest', save)
    assert run().success
    assert save.call_count == 3  # initial state and two committed videos
    assert sum('media_items' in snapshot for snapshot in snapshots) == 3
    transient = [snapshot for snapshot in snapshots if snapshot.get('media_progress_reset')]
    assert len(transient) == 2 and all('media_items' not in snapshot for snapshot in transient)


def test_discovery_failure_on_resume_keeps_committed_paths(batch, monkeypatch):
    run, save, _, calls, _, _, _ = batch
    first = run(lambda *a, **kw: save(*a, **kw) if not calls else DownloadResult(False, 'fail'))
    monkeypatch.setattr(media_batch, 'discover_media', Mock(side_effect=ValueError('authentication failed')))
    second = run(resume=True)
    assert not second.success and second.final_paths == first.final_paths
    assert Path(second.final_path).exists() and calls == ['a']


def test_changed_remote_post_keeps_previous_completed_result(batch):
    run, save, entries, calls, _, _, _ = batch
    first = run(lambda *a, **kw: save(*a, **kw) if not calls else DownloadResult(False, 'fail'))
    entries.pop(0)
    second = run(resume=True)
    assert second.success and first.final_path in second.final_paths
    assert len(second.final_paths) == 2


def test_untrusted_child_output_is_not_accepted(batch, tmp_path):
    run, _, _, _, _, workspace, _ = batch
    source = workspace / 'unfinished.mp4'
    source.write_bytes(b'not committed')
    result = run(lambda *a, **kw: DownloadResult(True, 'ok', str(source)))
    assert not result.success and not result.final_paths and source.exists()


def test_public_runner_uses_batch_for_non_youtube(monkeypatch, tmp_path):
    monkeypatch.setattr(runner, 'get_ytdlp_path', lambda: 'engine')
    monkeypatch.setattr(runner, 'get_download_folder', lambda _: str(tmp_path))
    monkeypatch.setattr(runner, 'get_ffmpeg_path', lambda: None)
    monkeypatch.setattr(runner, '_build_all_options', lambda *a, **kw: {'temp_path': str(tmp_path)})
    execute = Mock(return_value=DownloadResult(True, 'ok', 'a', ('a', 'b')))
    monkeypatch.setattr(media_batch, 'run_media_batch', execute)
    assert runner.download_video_with_result('https://x.com/post', {}, Mock()).final_paths == ('a', 'b')
    assert execute.call_args.args[-1] is runner.download_single_video_with_result


def test_public_runner_preserves_youtube_path(monkeypatch):
    single = Mock(return_value=DownloadResult(True, 'ok', 'youtube.mp4'))
    monkeypatch.setattr(runner, 'download_single_video_with_result', single)
    assert runner.download_video_with_result('https://www.youtube.com/watch?v=abc', {}, Mock()).success
    single.assert_called_once()
