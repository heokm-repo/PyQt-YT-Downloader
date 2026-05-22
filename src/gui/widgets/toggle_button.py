"""
재생/정지 토글 버튼 위젯
"""
import qtawesome as qta
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor
from resources.styles import (
    COLOR_DOWNLOADING, COLOR_PAUSED, COLOR_PRIMARY, COLOR_DEEP_ORANGE
)


class ToggleButton(QPushButton):
    """재생/정지 토글 버튼 (QtAwesome 아이콘 사용)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = True  # True: 재생 상태, False: 정지 상태
        self._hover = False
        self.setCursor(Qt.PointingHandCursor)
        self.update_icon()
        
    def setPlaying(self, playing):
        """재생/정지 상태 설정"""
        self._is_playing = playing
        self.update_icon()
    
    def isPlaying(self):
        return self._is_playing
    
    def enterEvent(self, event):
        self._hover = True
        self.update_icon()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        self.update_icon()
        super().leaveEvent(event)
    
    def update_icon(self):
        size = min(self.width(), self.height())
        icon_size = int(size * 1.2) if size > 0 else 60
            
        if self._is_playing:
            bg_color = QColor(COLOR_DOWNLOADING).darker(110).name() if self._hover else COLOR_DOWNLOADING
            icon_color = COLOR_PRIMARY
            self.setIcon(qta.icon('ri.play-circle-line', color=icon_color))
        else:
            bg_color = QColor(COLOR_PAUSED).darker(110).name() if self._hover else COLOR_PAUSED
            icon_color = COLOR_DEEP_ORANGE
            self.setIcon(qta.icon('ri.stop-circle-line', color=icon_color))
            
        self.setIconSize(QSize(icon_size, icon_size))
        
        margin = 5
        radius = (size - margin * 2) // 2 if size > 0 else 20
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                border-radius: {radius}px;
                margin: {margin}px;
                border: none;
            }}
        """)
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_icon()
