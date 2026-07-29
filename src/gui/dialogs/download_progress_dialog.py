"""Progress dialog for initial external binary downloads and binary updates."""
from PyQt5.QtCore import QThread, QTimer, pyqtSignal

from gui.dialogs.progress_dialog_base import ProgressDialogBase

from constants import DOWNLOAD_DIALOG_AUTO_CLOSE_MS
from locales.strings import STR
from utils.logger import log


class DownloadWorker(QThread):
    """Worker that downloads binaries in the background."""

    progress = pyqtSignal(str, int, int)  # binary_name, downloaded, total
    finished = pyqtSignal(bool)  # success

    def __init__(self, update_mode=False, updates=None, binary_names=None):
        super().__init__()
        self.update_mode = update_mode
        self.updates = updates  # Binaries to update.
        self.binary_names = (
            tuple(binary_names) if binary_names is not None else None
        )
        self.is_cancelled = False

    def cancel(self):
        """Request download cancellation."""
        self.is_cancelled = True

    def check_cancel(self):
        """Return whether cancellation was requested."""
        return self.is_cancelled

    def run(self):
        """Run the download workflow."""
        try:
            def progress_callback(binary_name, downloaded, total):
                self.progress.emit(binary_name, downloaded, total)

            if self.update_mode:
                from utils.bin.manager import update_binaries

                # Pass the selected binary update set.
                results = update_binaries(progress_callback, self.updates, self.check_cancel)
                success = all(results.values())
            else:
                from utils.bin.manager import download_initial_binaries

                success = download_initial_binaries(
                    progress_callback,
                    self.check_cancel,
                    binary_names=self.binary_names,
                )

            self.finished.emit(False if self.is_cancelled else success)

        except Exception as e:
            log.error(f"Download worker error: {e}")
            self.finished.emit(False)


class DownloadProgressDialog(ProgressDialogBase):
    """Progress dialog for initial binary downloads and binary updates."""

    def __init__(
        self,
        parent=None,
        update_mode=False,
        updates=None,
        binary_names=None,
    ):
        self.update_mode = update_mode
        self.updates = updates  # Binaries to update.
        self.binary_names = (
            tuple(binary_names) if binary_names is not None else None
        )
        title_text = STR.TITLE_APP_UPDATE if update_mode else STR.TITLE_INIT
        info_text = STR.MSG_UPDATE_DL if update_mode else STR.MSG_INIT_INFO

        super().__init__(
            parent=parent,
            title=title_text,
            status_text=STR.MSG_INIT_DESC,
            detail_text=STR.MSG_INIT_PREPARING,
            info_text=info_text,
        )

        self.worker = None
        self.download_success = False

    def cancel_download(self):
        """Cancel the download."""
        if self.worker and self.worker.isRunning():
            self.status_label.setText(STR.MSG_INIT_FAILED)
            self.detail_label.setText(STR.MSG_INIT_CANCELLING)
            self.cancel_btn.setEnabled(False)
            self.worker.cancel()
        else:
            self.reject()

    def start_download(self):
        """Start the download."""
        if self.worker is not None:
            return

        self.worker = DownloadWorker(
            self.update_mode,
            self.updates,
            self.binary_names,
        )
        self.worker.progress.connect(self._on_progress)
        self.worker.finished.connect(self._on_finished)
        self.worker.start()

        mode_text = "update" if self.update_mode else "initial download"
        log.info(f"Started binary {mode_text}")

    def _on_progress(self, binary_name: str, downloaded: int, total: int):
        """
        Update download progress.

        Args:
            binary_name: yt-dlp, the FFmpeg/ffprobe bundle, or quickjs.
            downloaded: Downloaded bytes.
            total: Total bytes.
        """
        if total > 0:
            percent = int((downloaded / total) * 100)
            bounded_percent = self.set_progress_value(percent)

            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)

            display_names = {
                "yt-dlp": "yt-dlp",
                "ffmpeg": "FFmpeg / ffprobe",
                "quickjs": "QuickJS",
            }
            display_name = display_names.get(binary_name, binary_name)
            self.status_label.setText(STR.MSG_INIT_DL_STATUS.format(item=display_name))
            self.detail_label.setText(
                f"{downloaded_mb:.1f} MB / {total_mb:.1f} MB ({bounded_percent}%)"
            )

    def _on_finished(self, success: bool):
        """
        Handle download completion.

        Args:
            success: Whether the download succeeded.
        """
        self.download_success = success

        if success:
            self.set_progress_value(100)
            self.status_label.setText(STR.MSG_INIT_COMPLETE)
            self.detail_label.setText(STR.MSG_INIT_STARTING)
            self.hide_cancel_button()
            log.info("Initial binary download completed successfully")

            QTimer.singleShot(DOWNLOAD_DIALOG_AUTO_CLOSE_MS, self.accept)

        elif self.worker and self.worker.is_cancelled:
            self.download_success = False
            self.status_label.setText(STR.MSG_INIT_FAILED)
            self.detail_label.setText(STR.MSG_INIT_DOWNLOAD_CANCELLED)
            log.info("Download cancelled by user")
            self.reject()

        else:
            self.status_label.setText(STR.MSG_INIT_FAILED)
            self.detail_label.setText(STR.ERR_INIT_DOWNLOAD)
            self.set_cancel_button_to_close()
            try:
                self.cancel_btn.clicked.disconnect()
            except (TypeError, RuntimeError) as e:
                log.debug(f"Cancel button was not connected or already cleaned up: {e}")
            self.cancel_btn.clicked.connect(self.reject)

            log.error("Initial binary download failed")

    def exec_(self):
        """Run the dialog and start downloading automatically."""
        self.start_download()
        return super().exec_()
