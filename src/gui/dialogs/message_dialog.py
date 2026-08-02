from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.dialogs.base_dialog import BaseDialog
from gui.widgets.button_sizing import set_text_button_minimum_width
from locales.strings import STR
from resources import styles
from resources.styles import (
    SETTINGS_FONT_FAMILY, MESSAGE_BTN_HEIGHT,
)

class MessageDialog(BaseDialog):
    """
    Styled Message Dialog replacing QMessageBox, inheriting from BaseDialog
    """
    # Dialog Types
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    
    def __init__(self, title, message, dialog_type=INFO, parent=None, show_cancel=False, buttons=None):
        icon_text = "mdi.information"
        if dialog_type == self.WARNING:
            icon_text = "mdi.alert"
        elif dialog_type == self.ERROR:
            icon_text = "mdi.close-circle"
        elif dialog_type == self.QUESTION:
            icon_text = "mdi.help-circle"

        show_close = not show_cancel and dialog_type != self.QUESTION and not buttons

        super().__init__(parent=parent, title=title, icon_text=icon_text, show_close_btn=show_close, show_divider=True)
        
        self.message = message
        self.dialog_type = dialog_type
        self.show_cancel = show_cancel
        self.custom_buttons = buttons
        self.clicked_button_index = None  # To track which custom button was clicked
        
        self._setup_content()
        self._setup_buttons()
        
    def _setup_content(self):
        # Message Body
        msg_label = QLabel(self.message)
        msg_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10))
        msg_label.setStyleSheet(styles.MESSAGE_BODY_STYLE)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Set minimum width for better look
        msg_label.setMinimumWidth(400) # Literal as requested
        self.content_layout.addWidget(msg_label)
        self.content_layout.addStretch()

    def _create_text_button(self, text, style, callback):
        btn = QPushButton(text)
        btn.setFixedHeight(MESSAGE_BTN_HEIGHT)
        set_text_button_minimum_width(btn)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        btn.setStyleSheet(style)
        return btn

    def _setup_buttons(self):
        if self.custom_buttons:
            for i, btn_config in enumerate(self.custom_buttons):
                text = btn_config.get('text', f'Button {i}')
                role = btn_config.get('role', 'action')
                style = (
                    styles.SETTINGS_SAVE_BUTTON_STYLE
                    if role == 'accept' or role == 'action'
                    else styles.SETTINGS_CANCEL_BUTTON_STYLE
                )
                btn = self._create_text_button(
                    text,
                    style,
                    lambda checked=False, idx=i, r=role: self._on_custom_button_clicked(idx, r),
                )
                self.button_layout.addWidget(btn)

        elif self.dialog_type == self.QUESTION:
            no_btn = self._create_text_button(
                STR.BTN_NO,
                styles.SETTINGS_CANCEL_BUTTON_STYLE,
                self.reject,
            )
            self.button_layout.addWidget(no_btn)

            yes_btn = self._create_text_button(
                STR.BTN_YES,
                styles.SETTINGS_SAVE_BUTTON_STYLE,
                self.accept,
            )
            self.button_layout.addWidget(yes_btn)

        elif self.show_cancel:
            cancel_btn = self._create_text_button(
                STR.BTN_CANCEL,
                styles.SETTINGS_CANCEL_BUTTON_STYLE,
                self.reject,
            )
            self.button_layout.addWidget(cancel_btn)

            ok_btn = self._create_text_button(
                STR.BTN_OK,
                styles.SETTINGS_SAVE_BUTTON_STYLE,
                self.accept,
            )
            self.button_layout.addWidget(ok_btn)

        else:
            ok_btn = self._create_text_button(
                STR.BTN_OK,
                styles.SETTINGS_SAVE_BUTTON_STYLE,
                self.accept,
            )
            self.button_layout.addWidget(ok_btn)

    def _on_custom_button_clicked(self, index, role):
        self.clicked_button_index = index
        if role == 'reject' or role == 'cancel':
            self.reject()
        else:
            self.accept()
