"""Styled progress dialog for application self-updates."""

from gui.dialogs.progress_dialog_base import ProgressDialogBase
from locales.strings import STR


class AppUpdateProgressDialog(ProgressDialogBase):
    """Application update download progress dialog using the app's own styling."""

    def __init__(self, parent=None):
        self._cancelled = False
        super().__init__(
            parent=parent,
            title=STR.TITLE_APP_UPDATE,
            status_text=STR.MSG_UPDATE_DL_STATUS,
            detail_text=STR.MSG_UPDATE_PREPARING,
            info_text=STR.MSG_UPDATE_DL,
            window_modal=True,
        )

    def cancel_download(self):
        self._cancelled = True
        self.status_label.setText(STR.MSG_UPDATE_CANCELLED)
        self.detail_label.setText(STR.MSG_INIT_CANCELLING)
        self.cancel_btn.setEnabled(False)

    def was_cancelled(self) -> bool:
        return self._cancelled

    def set_progress(self, percent: int):
        bounded_percent = self.set_progress_value(percent)
        self.detail_label.setText(f"{bounded_percent}%")

    def mark_installing(self):
        self.set_progress(100)
        self.status_label.setText(STR.MSG_UPDATE_INSTALLING)
        self.hide_cancel_button()
