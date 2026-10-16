from unittest.mock import Mock

from gui.dialogs.download_progress_dialog import DownloadWorker
from utils import download_progress
from utils.bin import manager


def test_per_binary_throttle_and_final_bytes(monkeypatch):
    monkeypatch.setattr(download_progress.time, 'monotonic', lambda: 0)

    def download(progress, check_cancel, binary_names=None):
        for name in ('yt-dlp', 'ffmpeg'):
            for size in range(1, 101):
                progress(name, size, 100)
        # Incorrect server length must not force every remaining notification.
        for size in range(1, 101):
            progress('quickjs', size, 3)
        return True

    monkeypatch.setattr(manager, 'download_initial_binaries', download)
    worker = DownloadWorker()
    notifications, finished = [], Mock()
    worker.progress.connect(lambda *args: notifications.append(args))
    worker.finished.connect(finished)
    worker.run()
    assert notifications == [
        ('yt-dlp', 1, 100), ('yt-dlp', 100, 100),
        ('ffmpeg', 1, 100), ('ffmpeg', 100, 100),
        ('quickjs', 1, 3), ('quickjs', 3, 3), ('quickjs', 100, 3),
    ]
    finished.assert_called_once_with(True)


def test_cancel_suppresses_pending_progress_and_success(monkeypatch):
    monkeypatch.setattr(download_progress.time, 'monotonic', lambda: 0)
    worker = DownloadWorker()

    def download(progress, check_cancel, binary_names=None):
        progress('yt-dlp', 1, 100)
        progress('yt-dlp', 2, 100)
        worker.cancel()
        assert check_cancel()
        progress('yt-dlp', 100, 100)
        return True

    monkeypatch.setattr(manager, 'download_initial_binaries', download)
    notifications, finished = [], Mock()
    worker.progress.connect(lambda *args: notifications.append(args))
    worker.finished.connect(finished)
    worker.run()
    assert notifications == [('yt-dlp', 1, 100)]
    finished.assert_called_once_with(False)
