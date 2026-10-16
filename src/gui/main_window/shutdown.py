"""Keep the window alive while its workers cooperatively stop."""
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


class WindowShutdown(QObject):
    ready_to_close = pyqtSignal()

    def __init__(self, window, scheduler, downloads):
        super().__init__(window)
        self.scheduler = scheduler
        self.downloads = downloads
        self.requested = False
        self.ready = False
        self.scheduler.stopped.connect(self._schedule_check)

    def begin(self):
        if self.requested:
            return
        self.requested = True
        worker = self.downloads.playlist_worker
        had_workers = bool(self.scheduler.workers) or worker is not None
        if worker and worker.isRunning():
            worker.finished.connect(self._schedule_check)
            worker.requestInterruption()
        self.scheduler.request_shutdown()
        if not had_workers:
            self.ready = True
        else:
            self._schedule_check()

    def _schedule_check(self):
        # Let already-queued completion/metadata signals run before final save.
        QTimer.singleShot(0, self._check)

    def _check(self):
        if not self.requested or self.ready:
            return
        worker = self.downloads.playlist_worker
        if self.scheduler.workers or (worker and worker.isRunning()):
            return
        self.ready = True
        self.ready_to_close.emit()
