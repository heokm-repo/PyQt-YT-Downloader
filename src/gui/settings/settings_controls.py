"""Reusable controls for the settings dialog."""

from typing import Callable, Mapping, Sequence

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QStandardItem
from PyQt5.QtWidgets import QLabel, QCheckBox, QComboBox, QHBoxLayout, QPushButton, QSpinBox

from constants import DEFAULT_FORMAT, MAX_DOWNLOADS_RANGE
from gui.settings.settings_form_data import language_display_options, language_index_for_code
from gui.settings.settings_format_options import build_format_combo_entries, normalize_format_selection
from resources.styles import (
    COLOR_DIVIDER,
    SETTINGS_CHECKBOX_STYLE,
    SETTINGS_COMBO_STYLE,
    SETTINGS_FONT_FAMILY,
    SETTINGS_INPUT_HEIGHT,
    SETTINGS_INPUT_STYLE,
    SETTINGS_LABEL_STYLE,
    SETTINGS_SECTION_FONT_SIZE,
    SETTINGS_SECTION_LABEL_STYLE,
)


def add_section_label(text: str, layout) -> None:
    """Add a styled section label to a settings layout."""
    label = QLabel(text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE, QFont.Bold))
    label.setStyleSheet(SETTINGS_SECTION_LABEL_STYLE)
    layout.addWidget(label)


def create_settings_label(text: str) -> QLabel:
    """Create a styled form label for settings rows."""
    label = QLabel(text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    label.setStyleSheet(SETTINGS_LABEL_STYLE)
    return label


def create_settings_combo(items: Sequence[str], current_value: str) -> QComboBox:
    """Create a styled combo box with an initial value."""
    combo = QComboBox()
    combo.addItems(list(items))
    combo.setCurrentText(current_value)
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(SETTINGS_COMBO_STYLE)
    return combo


def create_settings_checkbox(
    checked: bool, state_changed: Callable[[int], None] | None = None
) -> QCheckBox:
    """Create a styled settings checkbox."""
    checkbox = QCheckBox()
    checkbox.setChecked(checked)
    if state_changed:
        checkbox.stateChanged.connect(state_changed)
    checkbox.setStyleSheet(SETTINGS_CHECKBOX_STYLE)
    return checkbox


def create_max_downloads_spin(current_value: int) -> QSpinBox:
    """Create the max concurrent downloads spinbox."""
    spinbox = QSpinBox()
    spinbox.setRange(*MAX_DOWNLOADS_RANGE)
    spinbox.setValue(current_value)
    spinbox.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    spinbox.setStyleSheet(SETTINGS_INPUT_STYLE)
    return spinbox


def create_settings_button(
    spec,
    style_by_key: Mapping[str, str],
    callback_by_action: Mapping[str, Callable],
    fixed_size: tuple[int, int] | None = None,
    fixed_height: int | None = None,
) -> QPushButton:
    """Create a styled settings button from a button spec."""
    button = QPushButton(spec.label)
    button.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    button.setCursor(Qt.PointingHandCursor)
    if fixed_size:
        button.setFixedSize(*fixed_size)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    button.setStyleSheet(style_by_key[spec.style_key])
    button.clicked.connect(callback_by_action[spec.action])
    return button


def create_language_combo(language_code: str | None) -> QComboBox:
    """Create the language selection combo box."""
    combo = QComboBox()
    combo.addItems(language_display_options())
    combo.setCurrentIndex(language_index_for_code(language_code))
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(SETTINGS_COMBO_STYLE)
    return combo


def create_format_combo(
    current_format: str | None,
    video_header: str,
    audio_header: str,
    divider_color: str = COLOR_DIVIDER,
) -> QComboBox:
    """Create the output format combo box with non-selectable headers."""
    combo = QComboBox()
    model = combo.model()

    header_font = QFont()
    header_font.setBold(True)

    for entry in build_format_combo_entries(video_header, audio_header):
        if entry.is_header:
            header_item = QStandardItem(entry.label)
            header_item.setFont(header_font)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setEnabled(False)
            header_item.setBackground(QColor(divider_color))
            model.appendRow(header_item)
        else:
            combo.addItem(entry.label)

    combo.setCurrentText(normalize_format_selection(current_format or DEFAULT_FORMAT))
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(SETTINGS_COMBO_STYLE)
    return combo


def create_version_row(label_text: str, version_text: str) -> QHBoxLayout:
    """Create the app-version row for the app-management tab."""
    layout = QHBoxLayout()

    label = QLabel(label_text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))

    value_label = QLabel(version_text)
    value_label.setFont(QFont(SETTINGS_FONT_FAMILY, 14, QFont.Bold))
    value_label.setStyleSheet("color: #5F428B;")

    layout.addWidget(label)
    layout.addWidget(value_label)
    layout.addStretch()
    return layout
