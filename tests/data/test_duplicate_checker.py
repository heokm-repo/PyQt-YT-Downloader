from unittest.mock import Mock

import pytest

from constants import TaskStatus
from core.playlist_filter import filter_duplicate_videos
from data.duplicate_checker import DuplicateChecker
from data.models import DownloadTask


@pytest.mark.parametrize('status', list(TaskStatus))
def test_single_duplicate_preserves_active_status_and_first_match(status):
    tasks = [DownloadTask(i, '', status=status, extractor='Example', video_id='Case-ID', settings={'format': 'webm'})
             for i in (9, 2, 4)]
    history = Mock()
    history.is_downloaded.return_value = False
    result = DuplicateChecker(history).check('Example', 'Case-ID', 9, tasks, 'webm')
    active = status in (TaskStatus.WAITING, TaskStatus.DOWNLOADING, TaskStatus.PAUSED)
    assert result.is_duplicate == active
    assert result.duplicate_task is (tasks[1] if active else None)
    assert result.queue_status == (status if active else None)
    history.is_downloaded.assert_called_once_with('Example', 'Case-ID', 'webm')


@pytest.mark.parametrize('extractor,video_id,fmt', [
    ('example', 'Case-ID', 'mp4'), ('Example', 'case-id', 'mp4'), ('Example', 'Case-ID', 'mp3')])
def test_single_duplicate_requires_exact_extractor_id_and_format(extractor, video_id, fmt):
    history = Mock()
    history.is_downloaded.return_value = False
    task = DownloadTask(1, '', extractor='Example', video_id='Case-ID')
    assert not DuplicateChecker(history).check(extractor, video_id, -1, [task], fmt).is_duplicate


def test_history_and_queue_facts_are_both_preserved():
    history = Mock()
    history.is_downloaded.return_value = True
    task = DownloadTask(1, '', extractor='youtube', video_id='id', status=TaskStatus.PAUSED)
    result = DuplicateChecker(history).check('youtube', 'id', -1, [task])
    assert result.in_history and result.is_duplicate
    assert result.duplicate_task is task
    task.status = TaskStatus.FINISHED
    assert result.queue_status == TaskStatus.PAUSED


def test_playlist_scans_tasks_once_and_keeps_repeated_new_inputs():
    visits = []
    task = DownloadTask(1, '', extractor='youtube', video_id='queued')

    def tasks():
        visits.append(task.id)
        yield task

    history = Mock()
    history.find_downloaded_ids.return_value = {'old'}
    ids = ['new', 'old', 'queued', 'new', 'old']
    assert filter_duplicate_videos(ids, history, tasks(), 'mp4') == (['new', 'new'], 3)
    history.find_downloaded_ids.assert_called_once_with('youtube', ids, 'mp4')
    assert visits == [1]


def test_playlist_refreshes_keys_after_metadata_format_and_status_changes():
    history = Mock()
    history.find_downloaded_ids.return_value = set()
    task = DownloadTask(1, '', extractor='youtube', video_id='before')
    assert filter_duplicate_videos(['before'], history, [task], 'mp4') == ([], 1)
    task.video_id = 'after'
    assert filter_duplicate_videos(['before', 'after'], history, [task], 'mp4') == (['before'], 1)
    task.settings['format'] = 'mp3'
    assert filter_duplicate_videos(['after'], history, [task], 'mp4') == (['after'], 0)
    task.status = TaskStatus.FINISHED
    assert filter_duplicate_videos(['after'], history, [task], 'mp3') == (['after'], 0)


def test_empty_playlist_does_not_read_history_or_tasks():
    history = Mock()
    tasks = Mock()
    assert filter_duplicate_videos([], history, tasks, 'mp4') == ([], 0)
    history.find_downloaded_ids.assert_not_called()


def test_history_only_duplicates_do_not_scan_tasks():
    history = Mock()
    history.find_downloaded_ids.return_value = {'old'}
    assert filter_duplicate_videos(['old', 'old'], history, Mock(), 'mp4') == ([], 2)


def test_malformed_metadata_does_not_break_other_playlist_entries():
    history = Mock()
    history.find_downloaded_ids.return_value = set()
    task = DownloadTask(1, '', extractor='youtube', video_id=['malformed'])
    assert filter_duplicate_videos(['new'], history, [task], 'mp4') == (['new'], 0)
