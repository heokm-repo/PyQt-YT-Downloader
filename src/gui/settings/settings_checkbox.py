"""Theme-aware checkbox used by the settings dialog."""

from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import QCheckBox

from resources import colors


class SettingsCheckBox(QCheckBox):
    """Draw a compact checkbox without the platform's bright native surface."""

    _control_size = 18

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(self._control_size + 2, self._control_size + 2)
        self.setCursor(Qt.PointingHandCursor)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        offset = (min(self.width(), self.height()) - self._control_size) / 2
        indicator = QRectF(
            offset,
            offset,
            self._control_size,
            self._control_size,
        )

        if self.isChecked():
            fill_color = colors.COLOR_ACCENT
            border_color = colors.COLOR_ACCENT
        else:
            fill_color = colors.COLOR_CONTROL_SURFACE_ALT
            border_color = (
                colors.COLOR_ACCENT
                if self.underMouse() or self.hasFocus()
                else colors.COLOR_BORDER_HOVER
            )

        painter.setPen(QPen(QColor(border_color), 1))
        painter.setBrush(QColor(fill_color))
        painter.drawRoundedRect(indicator, 4, 4)

        if self.isChecked():
            check = QPainterPath()
            check.moveTo(QPointF(offset + 4.5, offset + 9.5))
            check.lineTo(QPointF(offset + 8, offset + 13))
            check.lineTo(QPointF(offset + 14, offset + 5.5))
            painter.setPen(
                QPen(
                    QColor(colors.COLOR_ON_ACCENT),
                    2,
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin,
                )
            )
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(check)

        painter.end()
