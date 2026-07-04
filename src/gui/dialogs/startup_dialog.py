from PyQt5.QtWidgets import QLabel, QProgressBar, QVBoxLayout
from PyQt5.QtCore import Qt

from gui.dialogs.base_dialog import BaseDialog
from resources.styles import STARTUP_DIALOG_WIDTH, STARTUP_DIALOG_HEIGHT, STARTUP_LABEL_STYLE, STARTUP_PROGRESS_STYLE
from constants import APP_TITLE
from locales.strings import STR
from core.workers import StartupWorker


class StartupDialog(BaseDialog):
    """Loading dialog shown during startup checks."""
    
    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            title=STR.TITLE_STARTUP,
            icon_text="mdi.rocket-launch",
            show_close_btn=False,  # Prevent closing while checks are running if needed.
            show_divider=True
        )
        self.setFixedSize(STARTUP_DIALOG_WIDTH, STARTUP_DIALOG_HEIGHT)
        
        self.worker = None
        self._setup_ui()
        
    def _setup_ui(self):
        # Status message label.
        self.status_label = QLabel(STR.MSG_STARTUP_CHECK_EXT)
        self.status_label.setStyleSheet(STARTUP_LABEL_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Indeterminate progress bar.
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(STARTUP_PROGRESS_STYLE)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0) # Indeterminate mode
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        
        self.content_layout.addLayout(layout)
        
    def start_checks(self):
        """Start background checks."""
        self.worker = StartupWorker()
        self.worker.status_updated.connect(self._on_status_updated)
        self.worker.finished_checks.connect(self._on_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()
        
    def _on_status_updated(self, msg: str):
        self.status_label.setText(msg)
        
    def _on_finished(self, updates_available: dict, app_update_info: tuple):
        """Store check results and close the dialog."""
        self.updates_available = updates_available
        self.app_update_info = app_update_info
        
        # Switch to the opening message and close without delay.
        self.status_label.setText(STR.MSG_STARTUP_OPENING)
        self.accept()
        
    def _on_error(self, err_msg: str):
        # Log errors only and let the main window open.
        from utils.logger import log
        log.error(f"Startup check error: {err_msg}")
        self.updates_available = {}
        self.app_update_info = (False, None, None)
        self.accept()
        
    def closeEvent(self, event):
        """Stop the worker if the user closes the dialog with Alt+F4 or similar."""
        if self.worker and self.worker.isRunning():
            self.worker.quit()
            self.worker.wait()
        super().closeEvent(event)
