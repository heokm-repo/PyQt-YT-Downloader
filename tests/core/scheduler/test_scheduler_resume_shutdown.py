import threading
from unittest.mock import Mock, patch

from core.download.result import DownloadResult
from core.scheduler import DownloadScheduler
from core.workers import DownloadWorker


def claimed_scheduler():
    scheduler = DownloadScheduler()
    generation = scheduler.add_task(1, 7, "url", {}, {})
    scheduler.download_queue.get_nowait()
    scheduler.download_queue.task_done()
    assert scheduler.claim_task(7, generation)
    return scheduler, generation


def test_resume_waits_for_previous_owner_then_executes_once():
    scheduler, generation = claimed_scheduler()
    scheduler.pause_task(7)
    scheduler.resume_task(7)
    scheduler.add_task(1, 7, "old-resume", {}, {}, True)
    scheduler.add_task(1, 7, "latest-resume", {}, {}, True)
    assert scheduler.download_queue.empty()
    scheduler.release_task(7, generation)
    worker = DownloadWorker(scheduler.download_queue, scheduler.stop_event,
                            scheduler.pause_event, scheduler)

    def download(url, *args, **kwargs):
        assert url == "latest-resume"
        scheduler.stop_event.set()
        return DownloadResult(True, "done")

    with patch("core.workers.download_handler.download_video_with_result", side_effect=download) as run:
        worker.run()
    run.assert_called_once()
    assert scheduler.download_queue.unfinished_tasks == 0
    assert not scheduler.is_task_running(7)


def test_cancel_discards_deferred_resume():
    scheduler, generation = claimed_scheduler()
    scheduler.add_task(1, 7, "resume", {}, {}, True)
    scheduler.cancel_task(7)
    scheduler.release_task(7, generation)
    assert scheduler.download_queue.empty()


def test_shutdown_wakes_paused_worker():
    scheduler = DownloadScheduler()
    scheduler.pause_all()
    entered_wait = threading.Event()
    original_wait = scheduler.pause_event.wait

    def wait(timeout=None):
        entered_wait.set()
        return original_wait(timeout)

    with patch.object(scheduler.pause_event, "wait", side_effect=wait):
        scheduler.initialize(1)
        worker = scheduler.workers[0]
        try:
            assert entered_wait.wait(2)
            assert scheduler.shutdown()
            assert not worker.isRunning()
        finally:
            scheduler.stop_event.set()
            scheduler.pause_event.set()
            worker.wait(2000)


def test_retiring_and_timed_out_workers_remain_tracked_until_stopped():
    scheduler = DownloadScheduler()
    worker = Mock(retire_flag=False)
    worker.isRunning.return_value = True
    worker.wait.return_value = False
    scheduler.workers = [worker]
    scheduler.adjust_worker_count(0)
    assert worker.retire_flag
    assert scheduler.workers == [worker]
    assert not scheduler.shutdown()
    worker.wait.assert_called_once()
    assert scheduler.workers == [worker]
    worker.isRunning.return_value = False
    assert scheduler.shutdown()
    assert scheduler.workers == []
