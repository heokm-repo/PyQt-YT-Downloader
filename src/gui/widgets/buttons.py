"""Shared button construction; sizing and presentation remain caller policies."""
from PyQt5.QtCore import QSize, Qt
from PyQt5.QtWidgets import QPushButton
import qtawesome as qta

from gui.widgets.button_sizing import set_text_button_minimum_width


def set_icon(button, name, color, size):
    button.setIcon(qta.icon(name, color=color))
    button.setIconSize(QSize(*size))


def create_button(callback, *, text='', style=None, font=None, fixed_size=None,
                  fixed_height=None, minimum_width=None, text_padding=None,
                  icon_name=None, icon_color=None, icon_size=None, tooltip=None,
                  auto_default=None, button_class=QPushButton):
    button = button_class()
    button.setText(text)
    if font is not None:
        button.setFont(font)
    if fixed_size is not None:
        button.setFixedSize(*fixed_size)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if minimum_width is not None:
        button.setMinimumWidth(minimum_width)
    if text_padding is not None:
        set_text_button_minimum_width(button, text_padding)
    if icon_name is not None:
        set_icon(button, icon_name, icon_color, icon_size)
    if tooltip is not None:
        button.setToolTip(tooltip)
    if auto_default is not None:
        button.setDefault(False)
        button.setAutoDefault(auto_default)
    button.setCursor(Qt.PointingHandCursor)
    if style is not None:
        button.setStyleSheet(style)
    button.clicked.connect(callback)
    return button
