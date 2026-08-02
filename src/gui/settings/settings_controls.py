"""Reusable controls for the settings dialog."""

from typing import Callable, Mapping, Sequence

from PyQt5.QtCore import QEvent, QRect, QSize, Qt
from PyQt5.QtGui import QColor, QFont, QIntValidator, QPainter, QStandardItem
from PyQt5.QtWidgets import QLabel, QCheckBox, QComboBox, QHBoxLayout, QLineEdit, QPushButton, QSizePolicy, QWidget

import qtawesome as qta

from constants import DEFAULT_FORMAT, MAX_DOWNLOADS_RANGE
from gui.settings.settings_form_data import (
    language_display_options,
    language_index_for_code,
    theme_index_for_value,
)
from gui.settings.settings_format_options import build_format_combo_entries, normalize_format_selection
from gui.settings.settings_checkbox import SettingsCheckBox
from gui.widgets.button_sizing import set_text_button_minimum_width
from resources import colors, styles
from resources.styles import (
    SETTINGS_FONT_FAMILY,
    SETTINGS_INPUT_HEIGHT,
    SETTINGS_SECTION_FONT_SIZE,
)


class SettingsComboBox(QComboBox):
    """Settings combo box with a QtAwesome menu-down arrow."""

    _arrow_size = 22
    _arrow_right_margin = 5

    def __init__(self):
        super().__init__()
        self._arrow_icon = qta.icon("mdi.menu-down", color=colors.COLOR_ICON_SUBDUED)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        size = QSize(self._arrow_size, self._arrow_size)
        x = self.width() - self._arrow_right_margin - size.width()
        y = (self.height() - size.height()) // 2
        painter.drawPixmap(QRect(x, y, size.width(), size.height()), self._arrow_icon.pixmap(size))
        painter.end()


class SettingsStepper(QWidget):
    """Compact minus/value/plus control for bounded integer settings."""

    _button_size = 28
    _icon_size = 18
    _value_width = 32

    def __init__(self, minimum: int, maximum: int, value: int):
        super().__init__()
        self._minimum = minimum
        self._maximum = maximum
        self._value = minimum
        self.setObjectName("SettingsStepper")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(SETTINGS_INPUT_HEIGHT)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(styles.SETTINGS_STEPPER_STYLE)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(0)

        self._minus_button = self._create_step_button("mdi.minus", -1)
        self._value_input = QLineEdit()
        self._value_input.setObjectName("SettingsStepperValue")
        self._value_input.setAlignment(Qt.AlignCenter)
        self._value_input.setMinimumWidth(self._value_width)
        self._value_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._value_input.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE, QFont.Bold))
        self._value_input.setValidator(QIntValidator(self._minimum, self._maximum, self))
        self._value_input.editingFinished.connect(self._commit_value_input)
        self._value_input.installEventFilter(self)
        self._plus_button = self._create_step_button("mdi.plus", 1)

        layout.addWidget(self._minus_button)
        layout.addWidget(self._value_input, 1)
        layout.addWidget(self._plus_button)
        self.setValue(value)

    def eventFilter(self, watched, event):
        if watched is self._value_input and event.type() == QEvent.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                self._commit_value_input()
                event.accept()
                return True
        return super().eventFilter(watched, event)

    def _create_step_button(self, icon_name: str, delta: int) -> QPushButton:
        button = QPushButton()
        button.setObjectName("SettingsStepperButton")
        button.setFixedSize(self._button_size, self._button_size)
        button.setCursor(Qt.PointingHandCursor)
        button.setIcon(qta.icon(icon_name, color=colors.COLOR_ICON_DEFAULT))
        button.setIconSize(QSize(self._icon_size, self._icon_size))
        button.clicked.connect(lambda: self.setValue(self._value + delta))
        return button

    def minimum(self) -> int:
        return self._minimum

    def maximum(self) -> int:
        return self._maximum

    def value(self) -> int:
        return self._value

    def setValue(self, value: int) -> None:
        self._value = max(self._minimum, min(self._maximum, int(value)))
        self._value_input.setText(str(self._value))
        self._update_button_state()

    def _commit_value_input(self) -> None:
        text = self._value_input.text().strip()
        try:
            value = self._minimum if not text else int(text)
        except ValueError:
            value = self._minimum
        self.setValue(value)

    def setEnabled(self, enabled: bool) -> None:
        super().setEnabled(enabled)
        self._update_button_state()

    def _update_button_state(self) -> None:
        enabled = self.isEnabled()
        self._minus_button.setEnabled(enabled and self._value > self._minimum)
        self._plus_button.setEnabled(enabled and self._value < self._maximum)


def add_section_label(text: str, layout) -> None:
    """Add a styled section label to a settings layout."""
    label = QLabel(text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE, QFont.Bold))
    label.setStyleSheet(styles.SETTINGS_SECTION_LABEL_STYLE)
    layout.addWidget(label)


def create_settings_label(text: str) -> QLabel:
    """Create a styled form label for settings rows."""
    label = QLabel(text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    label.setStyleSheet(styles.SETTINGS_LABEL_STYLE)
    return label


def create_settings_combo(items: Sequence[str], current_value: str) -> QComboBox:
    """Create a styled combo box with an initial value."""
    combo = SettingsComboBox()
    combo.addItems(list(items))
    combo.setCurrentText(current_value)
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(styles.SETTINGS_COMBO_STYLE)
    return combo


def create_settings_checkbox(
    checked: bool, state_changed: Callable[[int], None] | None = None
) -> QCheckBox:
    """Create a styled settings checkbox."""
    checkbox = SettingsCheckBox()
    checkbox.setChecked(checked)
    if state_changed:
        checkbox.stateChanged.connect(state_changed)
    checkbox.setStyleSheet(styles.SETTINGS_CHECKBOX_STYLE)
    return checkbox


def create_max_downloads_spin(current_value: int) -> SettingsStepper:
    """Create the max concurrent downloads stepper."""
    return SettingsStepper(*MAX_DOWNLOADS_RANGE, current_value)


def create_settings_button(
    spec,
    style_by_key: Mapping[str, str],
    callback_by_action: Mapping[str, Callable],
    fixed_size: tuple[int, int] | None = None,
    fixed_height: int | None = None,
    minimum_width_padding: int | None = None,
) -> QPushButton:
    """Create a styled settings button from a button spec."""
    button = QPushButton(spec.label)
    button.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))
    button.setCursor(Qt.PointingHandCursor)
    button.setDefault(False)
    button.setAutoDefault(False)
    if fixed_size:
        button.setFixedSize(*fixed_size)
    if fixed_height is not None:
        button.setFixedHeight(fixed_height)
    if minimum_width_padding is not None:
        set_text_button_minimum_width(button, minimum_width_padding)
    button.setStyleSheet(style_by_key[spec.style_key])
    button.clicked.connect(callback_by_action[spec.action])
    return button


def create_language_combo(language_code: str | None) -> QComboBox:
    """Create the language selection combo box."""
    combo = SettingsComboBox()
    combo.addItems(language_display_options())
    combo.setCurrentIndex(language_index_for_code(language_code))
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(styles.SETTINGS_COMBO_STYLE)
    return combo


def create_theme_combo(
    theme: str | None,
    light_label: str,
    dark_label: str,
) -> QComboBox:
    """Create the light/dark theme selection combo box."""
    combo = SettingsComboBox()
    combo.addItems([light_label, dark_label])
    combo.setCurrentIndex(theme_index_for_value(theme))
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(styles.SETTINGS_COMBO_STYLE)
    return combo


def create_format_combo(
    current_format: str | None,
    video_header: str,
    audio_header: str,
    divider_color: str | None = None,
) -> QComboBox:
    """Create the output format combo box with non-selectable headers."""
    combo = SettingsComboBox()
    model = combo.model()

    header_font = QFont()
    header_font.setBold(True)

    for entry in build_format_combo_entries(video_header, audio_header):
        if entry.is_header:
            header_item = QStandardItem(entry.label)
            header_item.setFont(header_font)
            header_item.setTextAlignment(Qt.AlignCenter)
            header_item.setEnabled(False)
            header_item.setBackground(QColor(divider_color or colors.COLOR_DIVIDER))
            model.appendRow(header_item)
        else:
            combo.addItem(entry.label)

    combo.setCurrentText(normalize_format_selection(current_format or DEFAULT_FORMAT))
    combo.setFixedHeight(SETTINGS_INPUT_HEIGHT)
    combo.setStyleSheet(styles.SETTINGS_COMBO_STYLE)
    return combo


def set_compatibility_format_mode(combo: QComboBox, enabled: bool) -> None:
    """Limit an existing format combo to MP4 and MP3 while compatibility is on."""
    from constants import FORMAT_OPTIONS
    from gui.settings.settings_format_options import (
        COMPATIBILITY_FORMATS,
        normalized_compatibility_format,
    )

    if enabled:
        combo.setCurrentText(normalized_compatibility_format(combo.currentText()))

    model = combo.model()
    for row in range(model.rowCount()):
        item = model.item(row)
        if item is None:
            continue
        label = item.text().strip().lower()
        if label in FORMAT_OPTIONS:
            item.setEnabled(not enabled or label in COMPATIBILITY_FORMATS)


def create_version_row(label_text: str, version_text: str) -> QHBoxLayout:
    """Create the app-version row for the app-management tab."""
    layout = QHBoxLayout()

    label = QLabel(label_text)
    label.setFont(QFont(SETTINGS_FONT_FAMILY, SETTINGS_SECTION_FONT_SIZE))

    value_label = QLabel(version_text)
    value_label.setFont(QFont(SETTINGS_FONT_FAMILY, 14, QFont.Bold))
    value_label.setStyleSheet(f"color: {colors.COLOR_ACCENT};")

    layout.addWidget(label)
    layout.addWidget(value_label)
    layout.addStretch()
    return layout
