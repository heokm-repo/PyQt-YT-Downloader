"""
재생/정지 토글 버튼 위젯
"""
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QPainterPath, QBrush, QPen


class ToggleButton(QPushButton):
    """재생/정지 토글 버튼 (QPainter로 아이콘 직접 그리기)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = True  # True: 재생 상태 (▶ 표시), False: 정지 상태 (■ 표시)
        self._bg_color_play = QColor("#DBC4F0")  # 재생 상태 배경색
        self._bg_color_stop = QColor("#FFE0B2")  # 정지 상태 배경색
        self._icon_color_play = QColor("#5F428B")  # 재생 아이콘 색상
        self._icon_color_stop = QColor("#E65100")  # 정지 아이콘 색상
        self._border_color_play = QColor("#5F428B")  # 재생 상태 테두리 색상
        self._border_color_stop = QColor("#E65100")  # 정지 상태 테두리 색상
        self._hover = False
        
    def setPlaying(self, playing):
        """재생/정지 상태 설정"""
        self._is_playing = playing
        self.update()
    
    def isPlaying(self):
        return self._is_playing
    
    def enterEvent(self, event):
        self._hover = True
        self.update()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._hover = False
        self.update()
        super().leaveEvent(event)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 배경 그리기
        if self._is_playing:
            bg_color = self._bg_color_play.darker(110) if self._hover else self._bg_color_play
            icon_color = self._icon_color_play
            border_color = self._border_color_play
        else:
            bg_color = self._bg_color_stop.darker(110) if self._hover else self._bg_color_stop
            icon_color = self._icon_color_stop
            border_color = self._border_color_stop
        
        # 원형 배경 + 테두리
        border_width = 1
        painter.setPen(QPen(border_color, border_width))
        painter.setBrush(QBrush(bg_color))
        # 테두리 두께만큼 안쪽으로 그려야 잘림 방지
        margin = border_width / 2
        rect = QRectF(margin, margin, self.width() - border_width, self.height() - border_width)
        painter.drawEllipse(rect)
        
        # 아이콘 그리기
        painter.setBrush(QBrush(icon_color))
        painter.setPen(Qt.NoPen)
        
        w = self.width()
        h = self.height()
        
        if self._is_playing:
            # 재생 아이콘 (삼각형 ▶) 크기
            icon_size = min(w, h) * 0.45  # 아이콘 크기
            center_x = w / 2
            center_y = h / 2
            
            # 정삼각형 좌표 (무게중심이 center에 오도록)
            # 삼각형 높이의 1/3 지점이 무게중심
            tri_height = icon_size
            tri_width = icon_size * 0.9
            
            # 무게중심 보정: 삼각형은 왼쪽이 뾰족하지 않으므로 오른쪽으로 약간 이동
            offset_x = tri_width * 0.1
            
            left_x = center_x - tri_width / 2 + offset_x
            right_x = center_x + tri_width / 2 + offset_x
            top_y = center_y - tri_height / 2
            bottom_y = center_y + tri_height / 2
            
            path = QPainterPath()
            path.moveTo(left_x, top_y)       # 왼쪽 상단
            path.lineTo(right_x, center_y)   # 오른쪽 중앙 (뾰족한 부분)
            path.lineTo(left_x, bottom_y)    # 왼쪽 하단
            path.closeSubpath()
            painter.drawPath(path)
        else:
            # 정지 아이콘 (사각형 ■) 크기
            icon_size = min(w, h) * 0.425
            rect_size = icon_size * 0.8
            x = (w - rect_size) / 2
            y = (h - rect_size) / 2
            painter.drawRect(QRectF(x, y, rect_size, rect_size))
        
        painter.end()
