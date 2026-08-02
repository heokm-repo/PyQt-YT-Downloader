"""Shared styled progress dialog shell."""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QProgressBar, QPushButton

from gui.dialogs.base_dialog import BaseDialog
from gui.widgets.button_sizing import set_text_button_minimum_width
from locales.strings import STR
from resources import styles
from resources.styles import (
    DOWNLOAD_DIALOG_HEIGHT,
    DOWNLOAD_DIALOG_WIDTH,
    SETTINGS_FONT_FAMILY,
)


class ProgressDialogBase(BaseDialog):
    """Base dialog for styled progress workflows."""

    def __init__(
        self,
        parent=None,
        *,
        title: str,
        status_text: str,
        detail_text: str,
        info_text: str,
        window_modal: bool = False,
    ):
        super().__init__(
            parent=parent,
            title=title,
            icon_text=None,
            show_close_btn=False,
            show_divider=True,
        )

        self.setFixedSize(DOWNLOAD_DIALOG_WIDTH, DOWNLOAD_DIALOG_HEIGHT)
        if window_modal:
            self.setWindowModality(Qt.WindowModal)

        self._setup_progress_content(status_text, detail_text, info_text)
        self._setup_progress_buttons()

    def _setup_progress_content(self, status_text: str, detail_text: str, info_text: str):
        """Set up the shared progress dialog content."""
        self.status_label = QLabel(status_text)
        self.status_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10))
        self.status_label.setStyleSheet(styles.SETTINGS_LABEL_STYLE)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        self.content_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setFixedHeight(25)
        self.progress_bar.setStyleSheet(styles.PROGRESS_BAR_STYLE)
        self.content_layout.addWidget(self.progress_bar)

        self.detail_label = QLabel(detail_text)
        self.detail_label.setFont(QFont(SETTINGS_FONT_FAMILY, 9))
        self.detail_label.setStyleSheet(styles.DETAIL_LABEL_STYLE)
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.detail_label)

        self.info_label = QLabel(info_text)
        self.info_label.setFont(QFont(SETTINGS_FONT_FAMILY, 8))
        self.info_label.setStyleSheet(styles.INFO_LABEL_STYLE)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setWordWrap(True)
        self.content_layout.addWidget(self.info_label)

        self.content_layout.addStretch()

    def _setup_progress_buttons(self):
        """Set up the shared cancel button."""
        self.cancel_btn = QPushButton(STR.BTN_CANCEL)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        self.cancel_btn.setFixedHeight(30)
        set_text_button_minimum_width(self.cancel_btn)
        self.cancel_btn.setStyleSheet(styles.SETTINGS_CANCEL_BUTTON_STYLE)
        self.cancel_btn.clicked.connect(self.cancel_download)
        self.button_layout.addWidget(self.cancel_btn)

    def cancel_download(self):
        """Handle a cancel request from the shared cancel button."""
        raise NotImplementedError

    def set_progress_value(self, percent: int):
        """Set progress after bounding the percentage to the progress bar range."""
        bounded_percent = max(0, min(100, int(percent)))
        self.progress_bar.setValue(bounded_percent)
        return bounded_percent

    def hide_cancel_button(self):
        """Disable and hide the shared cancel button."""
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setVisible(False)

    def set_cancel_button_to_close(self):
        """Turn the shared cancel button into a close button."""
        self.cancel_btn.setText(STR.BTN_CLOSE)
        set_text_button_minimum_width(self.cancel_btn)
        self.cancel_btn.setEnabled(True)
