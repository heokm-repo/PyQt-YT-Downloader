"""Utilities for saving and restoring multi-window state under the window_states settings key."""
import os
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QRect

from utils.utils import get_user_data_path
from utils.logger import log

_SETTINGS_FILE = 'settings.json'
_WINDOW_STATES_KEY = 'window_states'


def _load_all_settings() -> dict:
    """Read the full settings.json file as a dictionary."""
    path = os.path.join(get_user_data_path(), _SETTINGS_FILE)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"설정 파일 로드 실패: {e}", exc_info=True)
    return {}


def _save_all_settings(data: dict):
    """Save the full settings.json file."""
    path = os.path.join(get_user_data_path(), _SETTINGS_FILE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"설정 파일 저장 실패: {e}", exc_info=True)


def _is_visible_on_any_screen(rect: QRect) -> bool:
    """Return whether the given rect is sufficiently visible on any monitor."""
    app = QApplication.instance()
    if not app:
        return True  # If there is no app instance, the check cannot run; allow it.

    desktop = app.desktop()
    if not desktop:
        return True

    for i in range(desktop.screenCount()):
        screen_rect = desktop.availableGeometry(i)
        # Check whether part of the window is visible on screen.
        overlap = screen_rect.intersected(rect)
        if overlap.width() >= 50 and overlap.height() >= 32:
            return True

    return False


def save_window_state(window_name: str, window):
    """
    Save a window state into settings.json.
    
    Args:
        window_name: Unique window name.
        window: QWidget instance exposing geometry() and isMaximized().
    """
    is_maximized = window.isMaximized()

    # When maximized, store normalGeometry() so restore size remains valid.
    if is_maximized:
        geo = window.normalGeometry()
    else:
        geo = window.geometry()

    state = {
        'x': geo.x(),
        'y': geo.y(),
        'width': geo.width(),
        'height': geo.height(),
        'maximized': is_maximized
    }

    all_settings = _load_all_settings()
    if _WINDOW_STATES_KEY not in all_settings:
        all_settings[_WINDOW_STATES_KEY] = {}

    all_settings[_WINDOW_STATES_KEY][window_name] = state
    _save_all_settings(all_settings)

    log.debug(f"Window state saved: {window_name} = {state}")


def load_window_state(window_name: str) -> dict | None:
    """
    Load a saved window state from settings.json.
    
    Args:
        window_name: Unique window name.
    
    Returns:
        A dict with x, y, width, height, and maximized, or None if no state was saved.
    """
    all_settings = _load_all_settings()
    states = all_settings.get(_WINDOW_STATES_KEY, {})
    return states.get(window_name)


def restore_window_state(window_name: str, window, default_width: int, default_height: int):
    """
    Apply a saved window state with safe restore behavior.
    
    If the saved position is off-screen, place the window at the center with the default size.
    
    Args:
        window_name: Unique window name.
        window: QWidget instance.
        default_width: Default width when no saved state exists.
        default_height: Default height.
    
    Returns:
        True when saved state was restored, False when defaults were used.
    """
    state = load_window_state(window_name)

    if state is None:
        # No saved state: center with the default size.
        _center_window(window, default_width, default_height)
        return False

    x = state.get('x', 100)
    y = state.get('y', 100)
    width = state.get('width', default_width)
    height = state.get('height', default_height)
    maximized = state.get('maximized', False)

    # Safety check: recenter if the saved position is off-screen.
    test_rect = QRect(x, y, width, height)
    if not _is_visible_on_any_screen(test_rect):
        log.info(f"Window '{window_name}' 위치가 화면 밖 → 중앙 초기화")
        _center_window(window, default_width, default_height)
        return False

    # Normal restore.
    window.setGeometry(x, y, width, height)

    if maximized:
        window.showMaximized()

    log.debug(f"Window state restored: {window_name} = {state}")
    return True


def _center_window(window, width: int, height: int):
    """Center the window on screen with the default size."""
    window.resize(width, height)

    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = (screen_geo.width() - width) // 2 + screen_geo.x()
            y = (screen_geo.height() - height) // 2 + screen_geo.y()
            window.move(x, y)
