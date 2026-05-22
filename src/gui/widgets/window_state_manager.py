"""
WindowStateManager — 다중 창 상태 저장/복원 유틸리티

settings.json에 'window_states' 키 아래 각 창(window_name)별로
위치(x, y), 크기(width, height), 최대화 여부(maximized)를 저장합니다.

안전 복원: 저장된 위치가 현재 모니터 밖이면 화면 중앙으로 초기화합니다.
"""
import os
import json
from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtCore import QRect

from utils.utils import get_user_data_path
from utils.logger import log

_SETTINGS_FILE = 'settings.json'
_WINDOW_STATES_KEY = 'window_states'


def _load_all_settings() -> dict:
    """settings.json 전체를 읽어 dict로 반환"""
    path = os.path.join(get_user_data_path(), _SETTINGS_FILE)
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        log.error(f"설정 파일 로드 실패: {e}", exc_info=True)
    return {}


def _save_all_settings(data: dict):
    """settings.json 전체를 저장"""
    path = os.path.join(get_user_data_path(), _SETTINGS_FILE)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.error(f"설정 파일 저장 실패: {e}", exc_info=True)


def _is_visible_on_any_screen(rect: QRect) -> bool:
    """
    주어진 rect가 적어도 하나의 모니터 화면 안에 충분히 보이는지 확인.
    창의 상단 32px과 좌측 50px 이상이 어떤 스크린에 걸쳐 있으면 True.
    """
    app = QApplication.instance()
    if not app:
        return True  # 앱이 없으면 체크 불가, 허용

    desktop = app.desktop()
    if not desktop:
        return True

    for i in range(desktop.screenCount()):
        screen_rect = desktop.availableGeometry(i)
        # 창의 일부(상단+좌측)가 스크린 안에 있는지 확인
        overlap = screen_rect.intersected(rect)
        if overlap.width() >= 50 and overlap.height() >= 32:
            return True

    return False


def save_window_state(window_name: str, window):
    """
    창의 현재 상태를 settings.json에 저장합니다.
    
    Args:
        window_name: 창의 고유 이름 (예: "MainWindow", "SettingsDialog")
        window: QWidget 인스턴스 (geometry(), isMaximized() 사용)
    """
    is_maximized = window.isMaximized()

    # 최대화 상태에서는 normalGeometry()를 사용하여 복원 시 정상 크기를 저장
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
    settings.json에서 창 상태를 읽어 반환합니다.
    
    Args:
        window_name: 창의 고유 이름
    
    Returns:
        {'x', 'y', 'width', 'height', 'maximized'} dict 또는 None (저장된 상태 없음)
    """
    all_settings = _load_all_settings()
    states = all_settings.get(_WINDOW_STATES_KEY, {})
    return states.get(window_name)


def restore_window_state(window_name: str, window, default_width: int, default_height: int):
    """
    저장된 상태를 창에 적용합니다. 안전 복원 로직 포함.
    
    저장된 위치가 모니터 밖이면 화면 중앙에 기본 크기로 배치합니다.
    
    Args:
        window_name: 창의 고유 이름
        window: QWidget 인스턴스
        default_width: 기본 너비 (저장된 상태가 없을 때 사용)
        default_height: 기본 높이
    
    Returns:
        True: 상태 복원 성공, False: 기본값 사용 (중앙 배치)
    """
    state = load_window_state(window_name)

    if state is None:
        # 저장된 상태 없음 → 기본 크기로 화면 중앙 배치
        _center_window(window, default_width, default_height)
        return False

    x = state.get('x', 100)
    y = state.get('y', 100)
    width = state.get('width', default_width)
    height = state.get('height', default_height)
    maximized = state.get('maximized', False)

    # 안전 검사: 저장된 위치가 모니터 밖이면 중앙으로 초기화
    test_rect = QRect(x, y, width, height)
    if not _is_visible_on_any_screen(test_rect):
        log.info(f"Window '{window_name}' 위치가 화면 밖 → 중앙 초기화")
        _center_window(window, default_width, default_height)
        return False

    # 정상 복원
    window.setGeometry(x, y, width, height)

    if maximized:
        window.showMaximized()

    log.debug(f"Window state restored: {window_name} = {state}")
    return True


def _center_window(window, width: int, height: int):
    """창을 화면 중앙에 기본 크기로 배치"""
    window.resize(width, height)

    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            screen_geo = screen.availableGeometry()
            x = (screen_geo.width() - width) // 2 + screen_geo.x()
            y = (screen_geo.height() - height) // 2 + screen_geo.y()
            window.move(x, y)
