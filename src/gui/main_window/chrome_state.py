"""Build visual state for the custom main-window chrome."""

from dataclasses import dataclass

MAXIMIZE_ICON_NAME = "mdi.window-maximize"
RESTORE_ICON_NAME = "mdi.window-restore"
TITLE_BAR_DOUBLE_CLICK_PADDING = 10
WINDOW_DRAG_START_DISTANCE = 4


@dataclass(frozen=True)
class WindowChromeState:
    is_maximized: bool
    central_style: str
    maximize_icon_name: str


def build_window_chrome_state(
    is_maximized: bool,
    normal_style: str,
    maximized_style: str,
) -> WindowChromeState:
    """Return the style and title-bar icon for a window state."""
    if is_maximized:
        return WindowChromeState(
            is_maximized=True,
            central_style=maximized_style,
            maximize_icon_name=RESTORE_ICON_NAME,
        )

    return WindowChromeState(
        is_maximized=False,
        central_style=normal_style,
        maximize_icon_name=MAXIMIZE_ICON_NAME,
    )


def should_start_window_drag(
    button: object,
    left_button: object,
    is_title_bar_position: bool,
) -> bool:
    """Return True when a mouse press can start window dragging."""
    return button == left_button and is_title_bar_position


def should_continue_window_drag(
    previous_position: object | None,
    buttons: object,
    left_button: object,
) -> bool:
    """Return True when a mouse move should continue window dragging."""
    return previous_position is not None and buttons == left_button


def has_window_drag_started(
    previous_position: object | None,
    current_position: object,
    threshold: int = WINDOW_DRAG_START_DISTANCE,
) -> bool:
    """Return True once a pending drag has moved far enough."""
    if previous_position is None:
        return False
    if threshold <= 0:
        return True

    delta = current_position - previous_position
    manhattan_length = getattr(delta, "manhattanLength", None)
    if callable(manhattan_length):
        return manhattan_length() >= threshold

    x = getattr(delta, "x", None)
    y = getattr(delta, "y", None)
    if callable(x) and callable(y):
        return abs(x()) + abs(y()) >= threshold

    return True


def should_toggle_maximize_from_double_click(
    button: object,
    left_button: object,
    y_position: int,
    title_bar_height: int,
    padding: int = TITLE_BAR_DOUBLE_CLICK_PADDING,
) -> bool:
    """Return True when a double-click should toggle maximized state."""
    return button == left_button and y_position <= title_bar_height + padding


def chrome_state_after_window_change(
    is_maximized: bool,
    is_minimized: bool,
    tracked_maximized: bool,
) -> bool | None:
    """Return the chrome maximized state to apply after a Qt window-state change."""
    if is_maximized and not tracked_maximized:
        return True
    if not is_maximized and not is_minimized and tracked_maximized:
        return False
    return None
