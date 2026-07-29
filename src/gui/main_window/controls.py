"""Reusable controls for the main window."""

from dataclasses import dataclass
from typing import Callable, Sequence

import qtawesome as qta
from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QLabel,
    QAction,
    QFrame,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QToolButton,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from gui.widgets.toggle_button import ToggleButton
from resources.styles import (
    APP_TITLE_COLOR,
    DOWNLOAD_BUTTON_FONT_FAMILY,
    DOWNLOAD_BUTTON_FONT_SIZE,
    DOWNLOAD_BUTTON_HEIGHT,
    DOWNLOAD_BUTTON_STYLE,
    EMPTY_LABEL_STYLE,
    EMPTY_STATE_FONT_FAMILY,
    EMPTY_STATE_FONT_SIZE,
    MIN_DOWNLOAD_BUTTON_WIDTH,
    MIN_STATUS_LABEL_WIDTH,
    MIN_TITLE_LABEL_WIDTH,
    MIN_URL_INPUT_WIDTH,
    PROGRESS_SLIDER_DEFAULT,
    PROGRESS_SLIDER_MAX,
    PROGRESS_SLIDER_MIN,
    PROGRESS_SLIDER_STYLE,
    SETTINGS_BUTTON_SIZE,
    SETTINGS_BUTTON_STYLE,
    STATUS_BAR_FONT_FAMILY,
    STATUS_BAR_FONT_SIZE,
    STATUS_CONTROL_HEIGHT,
    STATUS_COUNTER_HORIZONTAL_PADDING,
    STATUS_SORT_BUTTON_HORIZONTAL_PADDING,
    STATUS_SORT_BUTTON_ICON_SIZE,
    STATUS_SORT_BUTTON_MIN_WIDTH,
    STATUS_BAR_HEIGHT,
    STATUS_BAR_MARGINS,
    STATUS_BAR_SPACING,
    STATUS_BAR_STYLE,
    STATUS_COUNTER_STYLE,
    STATUS_LABEL_STYLE,
    STATUS_SORT_BUTTON_STYLE,
    STATUS_SORT_MENU_STYLE,
    TASK_LIST_MARGINS,
    TASK_LIST_MIN_HEIGHT,
    TASK_LIST_SPACING,
    TITLE_BAR_BUTTON_SIZE,
    TITLE_BAR_BUTTON_ICON_SIZE,
    TITLE_BAR_FONT_FAMILY,
    TITLE_BAR_FONT_SIZE,
    TITLE_BAR_HEIGHT,
    TITLE_BAR_MARGINS,
    TITLE_BAR_SPACING,
    TOGGLE_BUTTON_SIZE,
    URL_INPUT_CONTAINER_MARGINS,
    URL_INPUT_CONTAINER_SPACING,
    URL_INPUT_CONTAINER_STYLE,
    URL_INPUT_FONT_FAMILY,
    URL_INPUT_FONT_SIZE,
    URL_INPUT_HEIGHT,
    URL_INPUT_SECTION_HEIGHT,
    URL_INPUT_STYLE,
)


@dataclass(frozen=True)
class TitleBarControls:
    frame: QFrame
    title_label: QLabel
    minimize_button: QPushButton
    maximize_button: QPushButton
    close_button: QPushButton


@dataclass(frozen=True)
class MainContentControls:
    central_widget: QWidget
    main_layout: QVBoxLayout


@dataclass(frozen=True)
class UrlSectionControls:
    frame: QFrame
    toggle_button: ToggleButton
    url_input: QLineEdit
    download_button: QPushButton
    settings_button: QPushButton


@dataclass(frozen=True)
class TaskListSectionControls:
    scroll_area: QScrollArea
    scroll_content: QWidget
    task_layout: QVBoxLayout
    empty_label: QLabel


@dataclass(frozen=True)
class StatusBarControls:
    frame: QFrame
    sort_button: QToolButton
    status_label: QLabel
    progress_slider: QSlider
    counter_label: QLabel


DEFAULT_STATUS_SORT_OPTIONS: tuple[tuple[str, str], ...] = (
    ("newest", "Newest"),
    ("oldest", "Oldest"),
    ("status", "Status"),
)


class StatusSortButton(QToolButton):
    """Status-bar sort button that opens a compact menu."""

    sortChanged = pyqtSignal(str)
    _icon_size = STATUS_SORT_BUTTON_ICON_SIZE

    def __init__(
        self,
        sort_options: Sequence[tuple[str, str]] = DEFAULT_STATUS_SORT_OPTIONS,
    ):
        super().__init__()
        self._current_key = ""
        self._sort_options: list[tuple[str, str]] = []
        self._sort_actions: dict[str, QAction] = {}
        self._menu = QMenu(self)
        self._menu.setStyleSheet(STATUS_SORT_MENU_STYLE)

        self.setMenu(self._menu)
        self.setPopupMode(QToolButton.InstantPopup)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIcon(qta.icon("mdi.sort-variant", color="#666666"))
        self.setIconSize(QSize(self._icon_size, self._icon_size))
        self.setFixedHeight(STATUS_CONTROL_HEIGHT)
        self.setMinimumWidth(STATUS_SORT_BUTTON_MIN_WIDTH)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(STATUS_SORT_BUTTON_STYLE)
        self.setSortOptions(sort_options)

    def setSortOptions(self, sort_options: Sequence[tuple[str, str]]) -> None:
        """Replace menu options while keeping the current key when possible."""
        previous_key = self._current_key
        self._sort_options = list(sort_options)
        self._sort_actions.clear()
        self._menu.clear()

        for key, label in self._sort_options:
            action = QAction(label, self)
            action.setCheckable(True)
            action.setData(key)
            action.triggered.connect(
                lambda _checked=False, selected_key=key: self.setCurrentKey(selected_key, emit=True)
            )
            self._menu.addAction(action)
            self._sort_actions[key] = action

        keys = [key for key, _label in self._sort_options]
        if not keys:
            self._current_key = ""
            self.setText("")
            self.setFixedWidth(STATUS_SORT_BUTTON_MIN_WIDTH)
            return

        self.setCurrentKey(previous_key if previous_key in keys else keys[0], emit=False)

    def currentKey(self) -> str:
        return self._current_key


    def _resize_to_current_text(self) -> None:
        text_width = self.fontMetrics().boundingRect(self.text()).width()
        width = max(
            STATUS_SORT_BUTTON_MIN_WIDTH,
            text_width + STATUS_SORT_BUTTON_HORIZONTAL_PADDING,
        )
        self.setFixedWidth(width)

    def setCurrentKey(self, key: str, emit: bool = False) -> None:
        labels = dict(self._sort_options)
        if key not in labels:
            return

        changed = key != self._current_key
        self._current_key = key
        self.setText(labels[key])
        self.setToolTip(labels[key])
        self._resize_to_current_text()
        for action_key, action in self._sort_actions.items():
            action.setChecked(action_key == key)
        if emit and changed:
            self.sortChanged.emit(key)


class StatusCounterLabel(QLabel):
    """Right-aligned task count label that resizes to its current text."""

    def __init__(self, text: str = "0/0"):
        super().__init__()
        self.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setFont(QFont(STATUS_BAR_FONT_FAMILY, STATUS_BAR_FONT_SIZE))
        self.setStyleSheet(STATUS_COUNTER_STYLE)
        self.setText(text)

    def setText(self, text: str) -> None:
        super().setText(text)
        self._resize_to_current_text()

    def _resize_to_current_text(self) -> None:
        text_width = self.fontMetrics().boundingRect(self.text()).width()
        self.setFixedWidth(text_width + STATUS_COUNTER_HORIZONTAL_PADDING)


def set_button_icon(
    button: QPushButton,
    icon_name: str,
    color: str = "#999999",
    icon_size: tuple[int, int] = (TITLE_BAR_BUTTON_ICON_SIZE, TITLE_BAR_BUTTON_ICON_SIZE),
) -> None:
    """Apply a qtawesome icon to a button."""
    button.setIcon(qta.icon(icon_name, color=color))
    button.setIconSize(QSize(*icon_size))


def create_main_content_layout(
    style: str,
    margins: tuple[int, int, int, int],
    spacing: int,
) -> MainContentControls:
    """Create the central widget and primary vertical layout."""
    central_widget = QWidget()
    central_widget.setObjectName("CentralWidget")
    central_widget.setStyleSheet(style)

    main_layout = QVBoxLayout(central_widget)
    main_layout.setContentsMargins(*margins)
    main_layout.setSpacing(spacing)

    return MainContentControls(central_widget, main_layout)


def create_title_label(text: str) -> QLabel:
    """Create the main-window title label."""
    label = QLabel(text)
    label.setFont(QFont(TITLE_BAR_FONT_FAMILY, TITLE_BAR_FONT_SIZE, QFont.Bold))
    label.setStyleSheet(f"color: {APP_TITLE_COLOR};")
    label.setMinimumWidth(MIN_TITLE_LABEL_WIDTH)
    return label


def create_title_bar_button(
    icon_name: str,
    style: str,
    callback: Callable,
    color: str = "#999999",
) -> QPushButton:
    """Create a fixed-size icon button for the custom title bar."""
    button = QPushButton()
    set_button_icon(button, icon_name, color=color)
    button.setFixedSize(TITLE_BAR_BUTTON_SIZE, TITLE_BAR_BUTTON_SIZE)
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(callback)
    button.setStyleSheet(style)
    return button


def create_title_bar(
    title: str,
    frame_style: str,
    minimize_style: str,
    maximize_style: str,
    close_style: str,
    on_minimize: Callable,
    on_maximize: Callable,
    on_close: Callable,
) -> TitleBarControls:
    """Create the custom title bar and return controls the window updates later."""
    frame = QFrame()
    frame.setFixedHeight(TITLE_BAR_HEIGHT)
    frame.setStyleSheet(frame_style)

    layout = QHBoxLayout(frame)
    layout.setContentsMargins(*TITLE_BAR_MARGINS)
    layout.setSpacing(TITLE_BAR_SPACING)

    title_label = create_title_label(title)
    layout.addWidget(title_label)
    layout.addStretch(1)

    minimize_button = create_title_bar_button(
        "mdi.window-minimize",
        minimize_style,
        on_minimize,
    )
    layout.addWidget(minimize_button)

    maximize_button = create_title_bar_button(
        "mdi.window-maximize",
        maximize_style,
        on_maximize,
    )
    layout.addWidget(maximize_button)

    close_button = create_title_bar_button("mdi.window-close", close_style, on_close)
    layout.addWidget(close_button)

    return TitleBarControls(
        frame,
        title_label,
        minimize_button,
        maximize_button,
        close_button,
    )


def create_toggle_button(callback: Callable) -> ToggleButton:
    """Create the global download toggle button."""
    button = ToggleButton()
    button.setFixedSize(TOGGLE_BUTTON_SIZE, TOGGLE_BUTTON_SIZE)
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(callback)
    return button


def create_url_input(placeholder: str, on_return_pressed: Callable) -> QLineEdit:
    """Create the URL input field."""
    line_edit = QLineEdit()
    line_edit.setPlaceholderText(placeholder)
    line_edit.setFixedHeight(URL_INPUT_HEIGHT)
    line_edit.setMinimumWidth(MIN_URL_INPUT_WIDTH)
    line_edit.setFont(QFont(URL_INPUT_FONT_FAMILY, URL_INPUT_FONT_SIZE))
    line_edit.setStyleSheet(URL_INPUT_STYLE)
    line_edit.returnPressed.connect(on_return_pressed)
    return line_edit


def create_download_button(text: str, on_clicked: Callable) -> QPushButton:
    """Create the primary download button."""
    button = QPushButton(text)
    button.setFixedHeight(DOWNLOAD_BUTTON_HEIGHT)
    button.setMinimumWidth(MIN_DOWNLOAD_BUTTON_WIDTH)
    button.setFont(
        QFont(DOWNLOAD_BUTTON_FONT_FAMILY, DOWNLOAD_BUTTON_FONT_SIZE, QFont.Bold)
    )
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(on_clicked)
    button.setStyleSheet(DOWNLOAD_BUTTON_STYLE)
    return button


def create_settings_button(on_clicked: Callable) -> QPushButton:
    """Create the settings icon button."""
    button = QPushButton()
    set_button_icon(button, "mdi.cog", color="#555555", icon_size=(26, 26))
    button.setFixedSize(SETTINGS_BUTTON_SIZE, SETTINGS_BUTTON_SIZE)
    button.setCursor(Qt.PointingHandCursor)
    button.clicked.connect(on_clicked)
    button.setStyleSheet(SETTINGS_BUTTON_STYLE)
    return button


def create_url_input_section(
    placeholder: str,
    download_text: str,
    on_toggle: Callable,
    on_download: Callable,
    on_settings: Callable,
) -> UrlSectionControls:
    """Create the URL input section and return controls the window updates later."""
    frame = QFrame()
    frame.setFixedHeight(URL_INPUT_SECTION_HEIGHT)
    frame.setStyleSheet(URL_INPUT_CONTAINER_STYLE)

    layout = QHBoxLayout(frame)
    layout.setContentsMargins(*URL_INPUT_CONTAINER_MARGINS)
    layout.setSpacing(URL_INPUT_CONTAINER_SPACING)

    toggle_button = create_toggle_button(on_toggle)
    layout.addWidget(toggle_button)

    url_input = create_url_input(placeholder, on_download)
    layout.addWidget(url_input, 1)

    button_group = QFrame()
    button_layout = QHBoxLayout(button_group)
    button_layout.setContentsMargins(0, 0, 0, 0)
    button_layout.setSpacing(0)

    download_button = create_download_button(download_text, on_download)
    button_layout.addWidget(download_button)

    settings_button = create_settings_button(on_settings)
    button_layout.addWidget(settings_button)

    layout.addWidget(button_group)

    return UrlSectionControls(
        frame,
        toggle_button,
        url_input,
        download_button,
        settings_button,
    )


def create_empty_state_label(text: str) -> QLabel:
    """Create the empty task-list label."""
    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setFont(QFont(EMPTY_STATE_FONT_FAMILY, EMPTY_STATE_FONT_SIZE))
    label.setStyleSheet(EMPTY_LABEL_STYLE)
    return label


def create_task_list_section(empty_text: str) -> TaskListSectionControls:
    """Create the task-list scroll area, content layout, and empty-state label."""
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setMinimumHeight(TASK_LIST_MIN_HEIGHT)
    scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("background: transparent; border: none;")

    scroll_content = QWidget()
    scroll_content.setStyleSheet("background: transparent;")

    task_layout = QVBoxLayout(scroll_content)
    task_layout.setContentsMargins(*TASK_LIST_MARGINS)
    task_layout.setSpacing(TASK_LIST_SPACING)
    task_layout.addStretch()

    scroll_area.setWidget(scroll_content)
    scroll_area.hide()

    empty_label = create_empty_state_label(empty_text)
    empty_label.setMinimumHeight(TASK_LIST_MIN_HEIGHT)

    return TaskListSectionControls(
        scroll_area,
        scroll_content,
        task_layout,
        empty_label,
    )


def create_status_label(text: str) -> QLabel:
    """Create the status bar text label."""
    label = QLabel(text)
    label.setFont(QFont(STATUS_BAR_FONT_FAMILY, STATUS_BAR_FONT_SIZE))
    label.setStyleSheet(STATUS_LABEL_STYLE)
    label.setMinimumWidth(MIN_STATUS_LABEL_WIDTH)
    return label


def create_progress_slider() -> QSlider:
    """Create the read-only status progress slider."""
    slider = QSlider(Qt.Horizontal)
    slider.setRange(PROGRESS_SLIDER_MIN, PROGRESS_SLIDER_MAX)
    slider.setValue(PROGRESS_SLIDER_DEFAULT)
    slider.setStyleSheet(PROGRESS_SLIDER_STYLE)
    slider.setEnabled(False)
    return slider


def create_status_sort_button(
    sort_options: Sequence[tuple[str, str]] = DEFAULT_STATUS_SORT_OPTIONS,
) -> StatusSortButton:
    """Create the task-list sort menu button for the status bar."""
    return StatusSortButton(sort_options)


def create_status_counter_label(text: str = "0/0") -> StatusCounterLabel:
    """Create the right-aligned task count label for the status bar."""
    return StatusCounterLabel(text)


def create_status_bar(
    status_text: str,
    sort_options: Sequence[tuple[str, str]] = DEFAULT_STATUS_SORT_OPTIONS,
    counter_text: str = "0/0",
) -> StatusBarControls:
    """Create the main-window status bar and return controls the window updates later."""
    frame = QFrame()
    frame.setFixedHeight(STATUS_BAR_HEIGHT)
    frame.setStyleSheet(STATUS_BAR_STYLE)

    layout = QHBoxLayout(frame)
    layout.setContentsMargins(*STATUS_BAR_MARGINS)
    layout.setSpacing(STATUS_BAR_SPACING)

    sort_button = create_status_sort_button(sort_options)
    layout.addWidget(sort_button)

    status_label = create_status_label(status_text)
    status_label.setParent(frame)
    status_label.hide()

    progress_slider = create_progress_slider()
    layout.addWidget(progress_slider, 1)

    counter_label = create_status_counter_label(counter_text)
    layout.addWidget(counter_label)

    return StatusBarControls(frame, sort_button, status_label, progress_slider, counter_label)
