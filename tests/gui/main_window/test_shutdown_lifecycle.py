import threading
import time
from unittest.mock import patch

import pytest
from PyQt5 import sip
from PyQt5.QtCore import QCoreApplication, QEvent, QTimer
from PyQt5.QtWidgets import QApplication

from constants import MSG_PAUSED_BY_USER, TaskStatus
from core.download.result import DownloadResult
from core.scheduler import DownloadScheduler
from core.workers import DownloadWorker, PlaylistAnalysisWorker
from gui.windows.main_window import YTDownloaderPyQt5
from utils.settings_store import default_settings


def spin(app, predicate, seconds=3):
    deadline = time.monotonic() + seconds
    while not predicate() and time.monotonic() < deadline:
        app.processEvents()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        time.sleep(.001)
    assert predicate()


def test_repeated_retirement_reclaims_qobjects_on_gui_thread():
    app = QApplication.instance() or QApplication([])
    scheduler = DownloadScheduler()
    references = []
    try:
        with patch('core.workers.QUEUE_TIMEOUT_SEC', .01):
            for _ in range(5):
                scheduler.adjust_worker_count(3)
                references.extend(scheduler.workers)
                scheduler.adjust_worker_count(0)
                spin(app, lambda: not scheduler.workers)
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                assert not scheduler.findChildren(DownloadWorker)
        assert all(sip.isdeleted(w) for w in references)
    finally:
        scheduler.shutdown()
        scheduler.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


@pytest.mark.parametrize('restart', [False, True])
@pytest.mark.parametrize('success', [False, True])
def test_close_keeps_event_loop_alive_and_saves_restarts_once(restart, success, tmp_path):
    app = QApplication.instance() or QApplication([])
    app.setQuitOnLastWindowClosed(False)
    with patch.object(YTDownloaderPyQt5, '_initialize_scheduler'), patch.object(YTDownloaderPyQt5, 'load_tasks_from_file'):
        window = YTDownloaderPyQt5(initial_settings=default_settings())
    window._restart_requested = restart
    entered = threading.Event()
    release = threading.Event()
    final_path = tmp_path / 'complete.mp4'
    final_path.write_bytes(b'verified fixture')
    task = window._create_and_register_task(7, 'offline', 'fixture')

    def download(*args, **kwargs):
        args[2]({'status': 'downloading', 'downloaded_bytes': 1, 'total_bytes': 2})
        entered.set()
        release.wait(3)
        return DownloadResult(success, 'done' if success else MSG_PAUSED_BY_USER,
                              str(final_path) if success else '')

    try:
        with patch('core.workers.download_handler.download_video_with_result', side_effect=download), patch(
            'gui.windows.main_window.save_window_state'
        ) as save_window, patch.object(window.task_manager, 'save_tasks') as save_tasks, patch(
            'utils.app_restart.launch_restart', return_value=True
        ) as launch, patch.object(window.history_manager, 'add_to_history') as history:
            window.scheduler.initialize(1)
            assert entered.wait(2)
            for _ in range(3):
                window.close()
            assert window._shutdown.requested and not window._shutdown.ready
            save_tasks.assert_not_called()
            pulse = []
            QTimer.singleShot(0, lambda: pulse.append(True))
            spin(app, lambda: bool(pulse))
            release.set()
            spin(app, lambda: window._close_saved)
            window.close()
            save_window.assert_called_once()
            save_tasks.assert_called_once()
            assert task.status == (TaskStatus.FINISHED if success else TaskStatus.PAUSED)
            if success:
                assert task.output_path == str(final_path)
                history.assert_called_once()
            assert launch.call_count == int(restart)
            assert not window.scheduler.workers
            assert window.scheduler.download_queue.unfinished_tasks == 0
    finally:
        release.set()
        window.scheduler.shutdown()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_playlist_cancellation_propagates_and_suppresses_stale_result():
    app = QApplication.instance() or QApplication([])
    entered = threading.Event()
    worker = PlaylistAnalysisWorker('offline')
    emitted = []
    worker.analysis_finished.connect(lambda *args: emitted.append(args))

    def extract(url, stop_check):
        entered.set()
        deadline = time.monotonic() + 2
        while not stop_check() and time.monotonic() < deadline:
            time.sleep(.001)
        assert stop_check()
        return ['id'], True, '', 1

    with patch('core.workers.download_handler.extract_playlist_video_ids', side_effect=extract):
        worker.start()
        assert entered.wait(1)
        worker.requestInterruption()
        assert worker.wait(2000)
    app.processEvents()
    assert emitted == []
    worker.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)


def test_playlist_finished_objects_are_reclaimed_each_cycle():
    app = QApplication.instance() or QApplication([])
    with patch.object(YTDownloaderPyQt5, '_initialize_scheduler'), patch.object(YTDownloaderPyQt5, 'load_tasks_from_file'):
        window = YTDownloaderPyQt5(initial_settings=default_settings())
    try:
        with patch('core.workers.download_handler.extract_playlist_video_ids', return_value=(['id'], True, '', 1)), patch.object(
            window, 'on_playlist_analysis_finished'
        ):
            for _ in range(5):
                window._handle_playlist_download('offline')
                worker = window.playlist_worker
                spin(app, lambda: window.playlist_worker is None)
                QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
                assert sip.isdeleted(worker)
                assert not window.findChildren(PlaylistAnalysisWorker)
    finally:
        window.close()
        window.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
