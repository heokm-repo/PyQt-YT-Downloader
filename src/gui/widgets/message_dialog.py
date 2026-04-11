from PyQt5.QtWidgets import QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.widgets.base_dialog import BaseDialog
from locales.strings import STR
from constants import BTN_TEXT_CLOSE_X
from resources.styles import (
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE,
    SETTINGS_FONT_FAMILY, MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT,
    MESSAGE_BODY_STYLE
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
        icon_text = "ℹ️"
        if dialog_type == self.WARNING:
            icon_text = "⚠️"
        elif dialog_type == self.ERROR:
            icon_text = "❌"
        elif dialog_type == self.QUESTION:
            icon_text = "❓"

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
        msg_label.setStyleSheet(MESSAGE_BODY_STYLE)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Set minimum width for better look
        msg_label.setMinimumWidth(400) # Literal as requested
        self.content_layout.addWidget(msg_label)
        self.content_layout.addStretch()

    def _setup_buttons(self):
        if self.custom_buttons:
            for i, btn_config in enumerate(self.custom_buttons):
                text = btn_config.get('text', f'Button {i}')
                role = btn_config.get('role', 'action')
                
                btn = QPushButton(text)
                btn.setFixedHeight(MESSAGE_BTN_HEIGHT) # Fixed height
                btn.setCursor(Qt.PointingHandCursor)
                
                # Style
                if role == 'accept' or role == 'action':
                    btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
                else: # cancel, reject
                    btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
                
                # Connect
                # Use default arguments to capture loop variable
                btn.clicked.connect(lambda checked, idx=i, r=role: self._on_custom_button_clicked(idx, r))
                self.button_layout.addWidget(btn)
                
        elif self.dialog_type == self.QUESTION:
            # Yes / No
            no_btn = QPushButton(STR.BTN_NO)
            no_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            no_btn.setCursor(Qt.PointingHandCursor)
            no_btn.clicked.connect(self.reject)
            no_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
            self.button_layout.addWidget(no_btn)
            
            yes_btn = QPushButton(STR.BTN_YES)
            yes_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            yes_btn.setCursor(Qt.PointingHandCursor)
            yes_btn.clicked.connect(self.accept)
            yes_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
            self.button_layout.addWidget(yes_btn)
            
        elif self.show_cancel:
            # OK / Cancel
            cancel_btn = QPushButton(STR.BTN_CANCEL)
            cancel_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(self.reject)
            cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
            self.button_layout.addWidget(cancel_btn)
            
            ok_btn = QPushButton(STR.BTN_OK)
            ok_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            ok_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
            self.button_layout.addWidget(ok_btn)
            
        else:
            # OK Only
            ok_btn = QPushButton(STR.BTN_OK)
            ok_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            # Use colored button for priority
            ok_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE) 
            self.button_layout.addWidget(ok_btn)

    def _on_custom_button_clicked(self, index, role):
        self.clicked_button_index = index
        if role == 'reject' or role == 'cancel':
            self.reject()
        else:
            self.accept()
