"""
공통 다이얼로그 기반 클래스
- 모든 커스텀 다이얼로그(설정, 메시지, 초기화 등)의 부모 클래스
- 프레임리스 윈도우, 그림자 효과, 드래그 이동 기능 제공
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QFont, QColor

from constants import BTN_TEXT_CLOSE_X
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_CLOSE_BUTTON_STYLE,
    SETTINGS_SHADOW_BLUR_RADIUS, SETTINGS_SHADOW_ALPHA,
    MESSAGE_TITLE_STYLE, SETTINGS_FONT_FAMILY, MESSAGE_DIVIDER_STYLE,
    SETTINGS_CONTAINER_MARGIN, SETTINGS_CONTENT_MARGIN, SETTINGS_CONTENT_SPACING
)

class BaseDialog(QDialog):
    """모든 디자인된 다이얼로그의 기본이 되는 클래스"""
    
    def __init__(self, parent=None, title="", icon_text=None, show_close_btn=True, show_divider=True):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.oldPos = None
        
        # Child classes should populate self.content_layout and self.button_layout
        self.content_layout = None
        self.button_layout = None
        self.container_layout = None # The layout of the main white container
        self.container = None
        
        self._setup_base_ui(title, icon_text, show_close_btn, show_divider)
        
    def _setup_base_ui(self, title_text, icon_text, show_close_btn, show_divider):
        # Main layout
        main_layout = QVBoxLayout(self)
        margin = SETTINGS_CONTAINER_MARGIN if 'SETTINGS_CONTAINER_MARGIN' in globals() else 10
        main_layout.setContentsMargins(margin, margin, margin, margin)
        
        # Container
        self.container = QFrame()
        self.container.setObjectName("Container")
        self.container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
        
        # Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(SETTINGS_SHADOW_BLUR_RADIUS if 'SETTINGS_SHADOW_BLUR_RADIUS' in globals() else 15)
        shadow.setColor(QColor(0, 0, 0, SETTINGS_SHADOW_ALPHA if 'SETTINGS_SHADOW_ALPHA' in globals() else 80))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)
        
        main_layout.addWidget(self.container)
        
        # Container Layout
        self.container_layout = QVBoxLayout(self.container)
        margins = SETTINGS_CONTENT_MARGIN if 'SETTINGS_CONTENT_MARGIN' in globals() else (15, 15, 15, 15)
        self.container_layout.setContentsMargins(*margins)
        spacing = SETTINGS_CONTENT_SPACING if 'SETTINGS_CONTENT_SPACING' in globals() else 10
        self.container_layout.setSpacing(spacing)
        
        # Title Bar
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        if icon_text:
            self.icon_label = QLabel(icon_text)
            self.icon_label.setFont(QFont("Segoe UI Emoji", 14))
            title_layout.addWidget(self.icon_label)
        else:
            self.icon_label = None
            
        self.title_label = QLabel(title_text)
        self.title_label.setFont(QFont(SETTINGS_FONT_FAMILY, 11, QFont.Bold))
        # fallback to basic style if not found
        self.title_label.setStyleSheet(MESSAGE_TITLE_STYLE if 'MESSAGE_TITLE_STYLE' in globals() else "color: #333333;")
        title_layout.addWidget(self.title_label)
        
        title_layout.addStretch()
        
        self.close_btn = None
        if show_close_btn:
            self.close_btn = QPushButton(BTN_TEXT_CLOSE_X)
            self.close_btn.setFixedSize(24, 24)
            self.close_btn.setCursor(Qt.PointingHandCursor)
            self.close_btn.clicked.connect(self.reject)
            self.close_btn.setStyleSheet(SETTINGS_CLOSE_BUTTON_STYLE)
            title_layout.addWidget(self.close_btn)
            
        self.container_layout.addLayout(title_layout)
        
        # Divider
        if show_divider:
            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setFrameShadow(QFrame.Sunken)
            line.setStyleSheet(MESSAGE_DIVIDER_STYLE if 'MESSAGE_DIVIDER_STYLE' in globals() else "background-color: #E2E8F0;")
            line.setFixedHeight(1)
            self.container_layout.addWidget(line)
        
        # Content Layout
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(15)
        self.container_layout.addLayout(self.content_layout)
        
        self.container_layout.addStretch()
        
        # Button Layout
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(10)
        self.button_layout.addStretch()
        self.container_layout.addLayout(self.button_layout)

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
