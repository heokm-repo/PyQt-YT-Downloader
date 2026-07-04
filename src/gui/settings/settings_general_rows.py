"""General-tab row construction helpers for the settings dialog."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton

from gui.widgets.button_sizing import set_text_button_minimum_width
from resources.styles import (
    SETTINGS_BROWSE_BUTTON_STYLE,
    SETTINGS_FONT_FAMILY,
    SETTINGS_INPUT_HEIGHT,
    SETTINGS_INPUT_STYLE,
    SETTINGS_LABEL_STYLE,
    SETTINGS_SECTION_FONT_SIZE,
)



def create_folder_picker_row(folder_path, browse_text, browse_callback):
    """Create the download-folder row and return its layout, line edit, and button."""
    layout = QHBoxLayout()
    layout.setSpacing(10)

    folder_line = QLineEdit(folder_path)
    folder_line.setReadOnly(True)
    folder_line.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    folder_line.setStyleSheet(SETTINGS_INPUT_STYLE)

    browse_button = QPushButton(browse_text)
    browse_button.setCursor(Qt.PointingHandCursor)
    browse_button.setDefault(False)
    browse_button.setAutoDefault(False)
    browse_button.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    browse_button.clicked.connect(browse_callback)
    browse_button.setStyleSheet(SETTINGS_BROWSE_BUTTON_STYLE)

    layout.addWidget(folder_line)
    layout.addWidget(browse_button)
    return layout, folder_line, browse_button


def create_login_row(label_text, button_text, login_callback):
    """Create the cookie/login row and return its layout."""
    layout = QHBoxLayout()
    layout.setSpacing(10)

    label = QLabel(label_text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    label.setStyleSheet(SETTINGS_LABEL_STYLE)
    layout.addWidget(label)

    layout.addStretch()

    login_button = QPushButton(button_text)
    login_button.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    set_text_button_minimum_width(login_button)
    login_button.setCursor(Qt.PointingHandCursor)
    login_button.setDefault(False)
    login_button.setAutoDefault(False)
    login_button.setStyleSheet(SETTINGS_BROWSE_BUTTON_STYLE)
    login_button.clicked.connect(login_callback)
    layout.addWidget(login_button)

    return layout
