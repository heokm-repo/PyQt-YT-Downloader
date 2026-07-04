"""Build visual state for the custom main-window chrome."""

from dataclasses import dataclass
from typing import Sequence

MAXIMIZE_ICON_NAME = "mdi.window-maximize"
RESTORE_ICON_NAME = "mdi.window-restore"
MAXIMIZED_LAYOUT_MARGINS = (15, 15, 15, 15)
TITLE_BAR_DOUBLE_CLICK_PADDING = 10


@dataclass(frozen=True)
class WindowChromeState:
    is_maximized: bool
    central_style: str
    layout_margins: tuple[int, int, int, int]
    maximize_icon_name: str


def build_window_chrome_state(
    is_maximized: bool,
    normal_style: str,
    maximized_style: str,
    normal_margins: Sequence[int],
) -> WindowChromeState:
    """Return the style, margins, and title-bar icon for a window state."""
    if is_maximized:
        return WindowChromeState(
            is_maximized=True,
            central_style=maximized_style,
            layout_margins=MAXIMIZED_LAYOUT_MARGINS,
            maximize_icon_name=RESTORE_ICON_NAME,
        )

    return WindowChromeState(
        is_maximized=False,
        central_style=normal_style,
        layout_margins=tuple(normal_margins),
        maximize_icon_name=MAXIMIZE_ICON_NAME,
    )


def should_continue_window_drag(
    previous_position: object | None,
    buttons: object,
    left_button: object,
) -> bool:
    """Return True when a mouse move should continue window dragging."""
    return previous_position is not None and buttons == left_button


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