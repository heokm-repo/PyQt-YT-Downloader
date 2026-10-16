"""Offline worker state and QObject lifetime probes."""
import time
import threading
from unittest.mock import patch
from .measurements import process_memory


def run_worker_probes(app):
    from PyQt5.QtCore import QCoreApplication, QEvent
    from core.scheduler import DownloadScheduler
    from core.workers import DownloadWorker
    from core.download.result import DownloadResult
    from constants import MSG_PAUSED_BY_USER

    results = {}
    for mode in ('success', 'failure', 'pause', 'exception'):
        scheduler = DownloadScheduler()
        worker = DownloadWorker(scheduler.download_queue, scheduler.stop_event,
                                scheduler.pause_event, scheduler)
        for task_id in range(1000):
            scheduler.add_task(1, task_id, 'offline', {}, {})
        scheduler.download_queue.put((100, -1, None))

        def download(*args, **kwargs):
            if mode == 'exception':
                raise RuntimeError('fixture failure')
            return DownloadResult(mode == 'success', MSG_PAUSED_BY_USER if mode == 'pause' else mode)

        with patch('core.workers.download_handler.download_video_with_result', side_effect=download), patch('core.workers.log'):
            worker.run()
        results[mode] = {'progress': len(worker.download_progress),
                         'timestamps': len(worker.last_update_times),
                         'claims': len(scheduler._active_task_generations),
                         'unfinished': scheduler.download_queue.unfinished_tasks}
        scheduler.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)

    scheduler = DownloadScheduler()
    cycles = []
    native_memory = [process_memory()]
    # Real QThreads; shorten idle queue polling only to keep this probe quick.
    with patch('core.workers.QUEUE_TIMEOUT_SEC', 0.01):
        for _ in range(10):
            scheduler.adjust_worker_count(3)
            scheduler.adjust_worker_count(0)
            for worker in list(scheduler.workers):
                assert worker.wait(2000)
            app.processEvents()
            QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
            cycles.append(len(scheduler.findChildren(DownloadWorker)))
            native_memory.append(process_memory())
        start = time.perf_counter()
        assert scheduler.shutdown()
        results['idle_shutdown_ms'] = (time.perf_counter() - start) * 1000
    results['qobjects_after_retirement'] = cycles
    results['native_memory_by_cycle'] = native_memory
    results['running_threads'] = sum(w.isRunning() for w in scheduler.findChildren(DownloadWorker))
    scheduler.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    scheduler = DownloadScheduler()
    entered = threading.Barrier(4)

    def busy_download(*args, **kwargs):
        entered.wait(timeout=3)
        scheduler.stop_event.wait(3)
        time.sleep(0.25)  # Controlled external-process cleanup delay.
        return DownloadResult(False, MSG_PAUSED_BY_USER)

    with patch('core.workers.download_handler.download_video_with_result', side_effect=busy_download):
        for i in range(3):
            scheduler.add_task(1, i, 'offline', {}, {})
        scheduler.initialize(3)
        entered.wait(timeout=3)
        start = time.perf_counter()
        if hasattr(scheduler, 'request_shutdown'):
            scheduler.request_shutdown()
        else:
            scheduler.shutdown()
        results['busy_shutdown_request_ms'] = (time.perf_counter()-start)*1000
        for worker in list(scheduler.workers):
            assert worker.wait(2000)
        assert scheduler.shutdown()
    app.processEvents()
    scheduler.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    return results
