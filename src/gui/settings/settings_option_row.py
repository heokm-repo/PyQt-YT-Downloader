"""Option-row construction helpers for the settings dialog."""

import qtawesome as qta
from PyQt5.QtCore import QPoint, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QToolTip

from resources.styles import (
    SETTINGS_FONT_FAMILY,
    SETTINGS_LABEL_STYLE,
    SETTINGS_SECTION_FONT_SIZE,
)

HELP_ICON_COLOR = "#5F428B"
HELP_ICON_NAME = "mdi.help-circle-outline"
HELP_ICON_SIZE = 22


def add_option_row(parent_layout, text, tooltip, checkbox) -> None:
    """Add a settings option row with a help tooltip and checkbox."""
    parent_layout.addLayout(create_option_row_layout(text, tooltip, checkbox))


def create_option_row_layout(text, tooltip, checkbox):
    """Create a settings option row layout."""
    row_layout = QHBoxLayout()
    row_layout.setSpacing(8)

    help_icon = _create_help_icon(tooltip)
    label = _create_option_label(text)

    row_layout.addWidget(help_icon)
    row_layout.addWidget(label)
    row_layout.addStretch()
    row_layout.addWidget(checkbox)
    return row_layout


def _create_help_icon(tooltip):
    help_icon = QLabel()
    help_pixmap = qta.icon(HELP_ICON_NAME, color=HELP_ICON_COLOR).pixmap(
        QSize(HELP_ICON_SIZE, HELP_ICON_SIZE)
    )
    help_icon.setPixmap(help_pixmap)
    help_icon.setFixedSize(HELP_ICON_SIZE, HELP_ICON_SIZE)

    def enter_event(event):
        QToolTip.showText(help_icon.mapToGlobal(QPoint(0, help_icon.height())), tooltip)

    def leave_event(event):
        QToolTip.hideText()

    help_icon.enterEvent = enter_event
    help_icon.leaveEvent = leave_event
    return help_icon


def _create_option_label(text):
    label = QLabel(text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    label.setStyleSheet(SETTINGS_LABEL_STYLE)
    return label