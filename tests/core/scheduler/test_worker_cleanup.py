import queue
from unittest.mock import patch

import pytest

from constants import MSG_PAUSED_BY_USER
from core.download.result import DownloadResult
from core.scheduler import DownloadScheduler
from core.workers import DownloadWorker


@pytest.mark.parametrize('mode', ['success', 'failure', 'pause', 'exception', 'init_error', 'queue_empty_error'])
def test_claimed_entries_release_state_and_queue_exactly_once(mode):
    scheduler = DownloadScheduler()
    worker = DownloadWorker(scheduler.download_queue, scheduler.stop_event, scheduler.pause_event, scheduler)
    for task_id in range(100):
        scheduler.add_task(1, task_id, 'url', {}, {})
    scheduler.download_queue.put((100, -1, None))
    original_init = worker._init_progress_tracking

    def initialize(*args):
        original_init(*args)
        if mode == 'init_error':
            raise RuntimeError('partial initialization')

    def download(*args, **kwargs):
        if mode in ('exception', 'queue_empty_error'):
            raise queue.Empty() if mode == 'queue_empty_error' else RuntimeError('fixture')
        return DownloadResult(mode == 'success', MSG_PAUSED_BY_USER if mode == 'pause' else mode)

    with patch.object(worker, '_init_progress_tracking', side_effect=initialize), patch(
        'core.workers.download_handler.download_video_with_result', side_effect=download
    ), patch('core.workers.log'), patch.object(scheduler, 'release_task', wraps=scheduler.release_task) as release, patch.object(
        scheduler.download_queue, 'task_done', wraps=scheduler.download_queue.task_done
    ) as done:
        worker.run()
    assert release.call_count == 100
    assert done.call_count == 101
    assert not worker.download_progress and not worker.last_update_times
    assert worker.current_task_id == -1 and worker.current_generation is None
    assert not scheduler._active_task_generations
    assert scheduler.download_queue.unfinished_tasks == 0
    assert len(scheduler.task_generations) == 100  # Keep generation tombstones.


@pytest.mark.parametrize('skip', ['stale', 'paused', 'cancelled', 'claim_denied', 'malformed'])
def test_unclaimed_entries_are_accounted_without_releasing_another_owner(skip):
    scheduler = DownloadScheduler()
    worker = DownloadWorker(scheduler.download_queue, scheduler.stop_event, scheduler.pause_event, scheduler)
    scheduler.add_task(1, 7, 'url', {}, {})
    if skip == 'stale':
        scheduler.task_generations[7] += 1
    elif skip == 'paused':
        scheduler.pause_task(7)
    elif skip == 'cancelled':
        scheduler.cancel_task(7)
    elif skip == 'malformed':
        scheduler.download_queue.get_nowait()
        scheduler.download_queue.task_done()
        scheduler.download_queue.put((1, 2, 3, 4))
    scheduler.download_queue.put((100, -1, None))
    with patch.object(scheduler, 'claim_task', return_value=False), patch.object(scheduler, 'release_task') as release, patch(
        'core.workers.log'
    ):
        worker.run()
    release.assert_not_called()
    assert scheduler.download_queue.unfinished_tasks == 0


def test_shutdown_requests_enqueue_wakes_once_and_keep_running_workers():
    from unittest.mock import Mock
    scheduler = DownloadScheduler()
    worker = Mock()
    worker.isRunning.return_value = True
    scheduler.workers = [worker]
    for _ in range(5):
        scheduler.request_shutdown()
    assert scheduler.download_queue.qsize() == 1
    worker.wait.assert_not_called()
    worker.deleteLater.assert_not_called()
    worker.isRunning.return_value = False
    scheduler._reap_finished_workers()
    assert scheduler.download_queue.unfinished_tasks == 0
    assert not scheduler.workers
    worker.deleteLater.assert_called_once()
