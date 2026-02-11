"""
Custom Message Dialog
- Replaces QMessageBox with a styled dialog matching the app's theme
- Supports Info, Warning, Error, Question types
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor

from locales.strings import STR
from constants import BTN_TEXT_CLOSE_X
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_TITLE_LABEL_STYLE, SETTINGS_CLOSE_BUTTON_STYLE,
    SETTINGS_CANCEL_BUTTON_STYLE, SETTINGS_SAVE_BUTTON_STYLE,
    # Moved Constants
    SETTINGS_FONT_FAMILY, SETTINGS_SHADOW_BLUR_RADIUS, SETTINGS_SHADOW_ALPHA,
    SETTINGS_DIALOG_WIDTH,
    # New Constants
    MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT,
    MESSAGE_TITLE_STYLE, MESSAGE_BODY_STYLE, MESSAGE_DIVIDER_STYLE
)

class MessageDialog(QDialog):
    """
    Styled Message Dialog replacing QMessageBox
    """
    # Dialog Types
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"
    
    def __init__(self, title, message, dialog_type=INFO, parent=None, show_cancel=False, buttons=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.show_cancel = show_cancel
        self.custom_buttons = buttons
        self.clicked_button_index = None  # To track which custom button was clicked
        self.oldPos = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Container
        container = QFrame()
        container.setObjectName("Container")
        container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 0)
        container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(container)
        
        # Content Layout
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 15, 20, 20)
        layout.setSpacing(15)
        
        # Title Bar
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon based on type
        icon_text = "ℹ️"
        if self.dialog_type == self.WARNING:
            icon_text = "⚠️"
        elif self.dialog_type == self.ERROR:
            icon_text = "❌"
        elif self.dialog_type == self.QUESTION:
            icon_text = "❓"
            
        icon_label = QLabel(icon_text)
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        title_layout.addWidget(icon_label)
        
        title_label = QLabel(self.title)
        title_label.setFont(QFont(SETTINGS_FONT_FAMILY, 11, QFont.Bold))
        title_label.setStyleSheet(MESSAGE_TITLE_STYLE)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Close button
        if not self.show_cancel and self.dialog_type != self.QUESTION and not self.custom_buttons:
             # Only show X button for info/error/warning where nice-to-have
             pass

        close_btn = QPushButton(STR.BTN_CLOSE)
        close_btn.setFixedSize(24, 24)
        close_btn.setText(BTN_TEXT_CLOSE_X)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.reject)
        close_btn.setStyleSheet(SETTINGS_CLOSE_BUTTON_STYLE)
        title_layout.addWidget(close_btn)
        
        layout.addLayout(title_layout)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet(MESSAGE_DIVIDER_STYLE)
        line.setFixedHeight(1)
        layout.addWidget(line)
        
        # Message Body
        msg_label = QLabel(self.message)
        msg_label.setFont(QFont(SETTINGS_FONT_FAMILY, 10))
        msg_label.setStyleSheet(MESSAGE_BODY_STYLE)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        # Set minimum width for better look
        msg_label.setMinimumWidth(400) # Literal as requested
        layout.addWidget(msg_label)
        
        layout.addStretch()
        
        # Button Section
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        
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
                btn_layout.addWidget(btn)
                
        elif self.dialog_type == self.QUESTION:
            # Yes / No
            no_btn = QPushButton(STR.BTN_NO)
            no_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            no_btn.setCursor(Qt.PointingHandCursor)
            no_btn.clicked.connect(self.reject)
            no_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
            btn_layout.addWidget(no_btn)
            
            yes_btn = QPushButton(STR.BTN_YES)
            yes_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            yes_btn.setCursor(Qt.PointingHandCursor)
            yes_btn.clicked.connect(self.accept)
            yes_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
            btn_layout.addWidget(yes_btn)
            
        elif self.show_cancel:
            # OK / Cancel
            cancel_btn = QPushButton(STR.BTN_CANCEL)
            cancel_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            cancel_btn.setCursor(Qt.PointingHandCursor)
            cancel_btn.clicked.connect(self.reject)
            cancel_btn.setStyleSheet(SETTINGS_CANCEL_BUTTON_STYLE)
            btn_layout.addWidget(cancel_btn)
            
            ok_btn = QPushButton(STR.BTN_OK)
            ok_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            ok_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE)
            btn_layout.addWidget(ok_btn)
            
        else:
            # OK Only
            ok_btn = QPushButton(STR.BTN_OK)
            ok_btn.setFixedSize(MESSAGE_BTN_WIDTH, MESSAGE_BTN_HEIGHT)
            ok_btn.setCursor(Qt.PointingHandCursor)
            ok_btn.clicked.connect(self.accept)
            # Use colored button for priority
            ok_btn.setStyleSheet(SETTINGS_SAVE_BUTTON_STYLE) 
            btn_layout.addWidget(ok_btn)
            
        layout.addLayout(btn_layout)

    def _on_custom_button_clicked(self, index, role):
        self.clicked_button_index = index
        if role == 'reject' or role == 'cancel':
            self.reject()
        else:
            self.accept()

    # Mouse Drag Events
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None
