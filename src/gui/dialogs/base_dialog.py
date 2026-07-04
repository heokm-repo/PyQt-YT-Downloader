"""
공통 다이얼로그 기반 클래스
- 모든 커스텀 다이얼로그(설정, 메시지, 초기화 등)의 부모 클래스
- 프레임리스 윈도우, 그림자 효과, 드래그 이동 기능 제공
- resizable=True 시 8방향 리사이징 + 최대화/복구 + 상태 저장 지원
"""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QFont, QColor
import qtawesome as qta

from constants import BTN_TEXT_CLOSE_X
from resources.styles import (
    SETTINGS_CONTAINER_STYLE, SETTINGS_CLOSE_BUTTON_STYLE,
    SETTINGS_SHADOW_BLUR_RADIUS, SETTINGS_SHADOW_ALPHA,
    MESSAGE_TITLE_STYLE, SETTINGS_FONT_FAMILY, MESSAGE_DIVIDER_STYLE,
    SETTINGS_CONTAINER_MARGIN, SETTINGS_CONTENT_MARGIN, SETTINGS_CONTENT_SPACING,
    SETTINGS_DIALOG_TITLE_ICON_SIZE, SETTINGS_DIALOG_TITLE_BUTTON_SIZE,
    SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE, MAXIMIZE_BUTTON_STYLE
)
from gui.windowing.resizable_mixin import ResizableMixin
from gui.windowing.window_state_manager import save_window_state, restore_window_state
from utils.logger import log

class BaseDialog(ResizableMixin, QDialog):
    """모든 디자인된 다이얼로그의 기본이 되는 클래스"""
    
    def __init__(self, parent=None, title="", icon_text=None, show_close_btn=True, 
                 show_divider=True, resizable=False, window_name=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.oldPos = None
        self._resizable = resizable
        self._window_name = window_name  # 상태 저장용 고유 이름
        self._is_maximized = False
        
        # Child classes should populate self.content_layout and self.button_layout
        self.content_layout = None
        self.button_layout = None
        self.container_layout = None # The layout of the main white container
        self.container = None
        self.maximize_btn = None
        
        # ResizableMixin 초기화
        self._init_resizable(enabled=resizable)
        
        self._setup_base_ui(title, icon_text, show_close_btn, show_divider)
        
    def _setup_base_ui(self, title_text, icon_text, show_close_btn, show_divider):
        self._main_layout = self._create_main_layout()
        self.container = self._create_container()
        self._apply_container_shadow()
        self._main_layout.addWidget(self.container)

        self.container_layout = self._create_container_layout()
        self.container_layout.addLayout(
            self._create_title_bar(title_text, icon_text, show_close_btn)
        )

        if show_divider:
            self.container_layout.addWidget(self._create_divider())

        self.content_layout = self._create_content_layout()
        self.container_layout.addLayout(self.content_layout)
        self.container_layout.addStretch()

        self.button_layout = self._create_button_layout()
        self.container_layout.addLayout(self.button_layout)

    def _create_main_layout(self):
        layout = QVBoxLayout(self)
        margin = SETTINGS_CONTAINER_MARGIN if 'SETTINGS_CONTAINER_MARGIN' in globals() else 10
        layout.setContentsMargins(margin, margin, margin, margin)
        return layout

    def _create_container(self):
        container = QFrame()
        container.setObjectName("Container")
        container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
        return container

    def _apply_container_shadow(self):
        shadow = QGraphicsDropShadowEffect(self)
        blur_radius = SETTINGS_SHADOW_BLUR_RADIUS if 'SETTINGS_SHADOW_BLUR_RADIUS' in globals() else 15
        shadow_alpha = SETTINGS_SHADOW_ALPHA if 'SETTINGS_SHADOW_ALPHA' in globals() else 80
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(0, 0, 0, shadow_alpha))
        shadow.setOffset(0, 0)
        self.container.setGraphicsEffect(shadow)

    def _create_container_layout(self):
        layout = QVBoxLayout(self.container)
        margins = SETTINGS_CONTENT_MARGIN if 'SETTINGS_CONTENT_MARGIN' in globals() else (15, 15, 15, 15)
        layout.setContentsMargins(*margins)
        spacing = SETTINGS_CONTENT_SPACING if 'SETTINGS_CONTENT_SPACING' in globals() else 10
        layout.setSpacing(spacing)
        return layout

    def _create_title_bar(self, title_text, icon_text, show_close_btn):
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)

        if icon_text:
            self.icon_label = self._create_icon_label(icon_text)
            title_layout.addWidget(self.icon_label)
        else:
            self.icon_label = None

        self.title_label = self._create_title_label(title_text)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        self.maximize_btn = self._create_maximize_button()
        if self.maximize_btn:
            title_layout.addWidget(self.maximize_btn)

        self.close_btn = self._create_close_button() if show_close_btn else None
        if self.close_btn:
            title_layout.addWidget(self.close_btn)

        return title_layout

    def _create_icon_label(self, icon_text):
        icon_label = QLabel()
        icon_pixmap = qta.icon(icon_text, color='#5F428B').pixmap(QSize(SETTINGS_DIALOG_TITLE_ICON_SIZE, SETTINGS_DIALOG_TITLE_ICON_SIZE))
        icon_label.setPixmap(icon_pixmap)
        icon_label.setFixedSize(SETTINGS_DIALOG_TITLE_ICON_SIZE, SETTINGS_DIALOG_TITLE_ICON_SIZE)
        return icon_label

    def _create_title_label(self, title_text):
        title_label = QLabel(title_text)
        title_label.setFont(QFont(SETTINGS_FONT_FAMILY, 11, QFont.Bold))
        style = MESSAGE_TITLE_STYLE if 'MESSAGE_TITLE_STYLE' in globals() else "color: #333333;"
        title_label.setStyleSheet(style)
        return title_label

    def _create_maximize_button(self):
        if not self._resizable:
            return None

        button = QPushButton()
        button.setIcon(qta.icon('mdi.window-maximize', color='#999999'))
        button.setIconSize(QSize(SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE, SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE))
        button.setFixedSize(SETTINGS_DIALOG_TITLE_BUTTON_SIZE, SETTINGS_DIALOG_TITLE_BUTTON_SIZE)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self._toggle_maximize)
        button.setStyleSheet(MAXIMIZE_BUTTON_STYLE)
        return button

    def _create_close_button(self):
        button = QPushButton()
        button.setIcon(qta.icon('mdi.window-close', color='#999999'))
        button.setIconSize(QSize(SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE, SETTINGS_DIALOG_TITLE_BUTTON_ICON_SIZE))
        button.setFixedSize(SETTINGS_DIALOG_TITLE_BUTTON_SIZE, SETTINGS_DIALOG_TITLE_BUTTON_SIZE)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(self.reject)
        button.setStyleSheet(SETTINGS_CLOSE_BUTTON_STYLE)
        return button

    def _create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        style = MESSAGE_DIVIDER_STYLE if 'MESSAGE_DIVIDER_STYLE' in globals() else "background-color: #E2E8F0;"
        line.setStyleSheet(style)
        line.setFixedHeight(1)
        return line

    def _create_content_layout(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)
        return layout

    def _create_button_layout(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)
        layout.addStretch()
        return layout
    # ── 최대화/복구 ──────────────────────────────────────

    def _toggle_maximize(self):
        """최대화 ↔ 복구 토글"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # ── 상태 저장/복원 ──────────────────────────────────

    def restore_state(self, default_width, default_height):
        """저장된 상태를 복원합니다. show() 전에 호출하세요."""
        if self._window_name:
            restore_window_state(self._window_name, self, default_width, default_height)

    def _save_state(self):
        """현재 상태를 저장합니다."""
        if self._window_name:
            save_window_state(self._window_name, self)

    # ── Mouse Events ──────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 리사이즈 우선
            if self._resizable and self.resizable_mouse_press(event):
                return
            # 리사이즈 영역이 아니면 드래그 이동
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        # 리사이즈 중이면 리사이즈 처리
        if self._resizable and self.resizable_mouse_move(event):
            return
        # 드래그 이동
        if self.oldPos is not None and event.buttons() == Qt.LeftButton:
            # 최대화 상태에서 드래그 시 복구 후 이동
            if self._is_maximized:
                self.showNormal()
                # 복구 후 마우스 위치를 기준으로 창 위치 조정
                self.oldPos = event.globalPos()
                return
            delta = QPoint(event.globalPos() - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self._resizable and self.resizable_mouse_release(event):
                return
            self.oldPos = None

    def changeEvent(self, event):
        """창 상태 변경 이벤트 감지 (에어로 스냅, 최대화 버튼 등 모두 포괄)"""
        from PyQt5.QtCore import QEvent
        if event.type() == QEvent.WindowStateChange:
            name = self._window_name or self.__class__.__name__
            if self.isMaximized() and not self._is_maximized:
                # OS에 의해 최대화됨 → 내부 상태 및 UI 동기화
                self._is_maximized = True
                self._main_layout.setContentsMargins(8, 8, 8, 8)
                self.container.setStyleSheet("""
                    QFrame#Container {
                        background-color: #FFFFFF;
                        border: none;
                        border-radius: 0px;
                    }
                    QLabel {
                        font-family: 'Segoe UI', sans-serif;
                        color: #333333;
                    }
                """)
                self.container.setGraphicsEffect(None)
                if self.maximize_btn:
                    self.maximize_btn.setIcon(qta.icon('mdi.window-restore', color='#999999'))
                log.info(f"창 최대화 됨 ({name})")
            elif not self.isMaximized() and not self.isMinimized() and self._is_maximized:
                # OS에 의해 복원됨 → 내부 상태 및 UI 동기화
                self._is_maximized = False
                margin = SETTINGS_CONTAINER_MARGIN if 'SETTINGS_CONTAINER_MARGIN' in globals() else 10
                self._main_layout.setContentsMargins(margin, margin, margin, margin)
                self.container.setStyleSheet(SETTINGS_CONTAINER_STYLE)
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(SETTINGS_SHADOW_BLUR_RADIUS)
                shadow.setColor(QColor(0, 0, 0, SETTINGS_SHADOW_ALPHA))
                shadow.setOffset(0, 0)
                self.container.setGraphicsEffect(shadow)
                if self.maximize_btn:
                    self.maximize_btn.setIcon(qta.icon('mdi.window-maximize', color='#999999'))
                log.info(f"창 기본 크기로 복구 됨 ({name})")
        super().changeEvent(event)

    def mouseDoubleClickEvent(self, event):
        """타이틀 바 더블클릭 → 최대화/복구"""
        if self._resizable and event.button() == Qt.LeftButton:
            # 타이틀 바 영역에서만 동작 (상단 40px 이내)
            if event.pos().y() <= 40:
                self._toggle_maximize()
                return
        super().mouseDoubleClickEvent(event)

    # ── 닫기 시 상태 저장 ─────────────────────────────

    def closeEvent(self, event):
        if self._resizable:
            self._save_state()
        super().closeEvent(event)

    def reject(self):
        if self._resizable:
            self._save_state()
        super().reject()

    def accept(self):
        if self._resizable:
            self._save_state()
        super().accept()
