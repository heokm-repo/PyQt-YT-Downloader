"""
ResizableMixin — Frameless 윈도우의 8방향 마우스 리사이징 믹스인

순수 Qt 이벤트 방식이 아닌, Win32 API와 nativeEvent를 활용한 방식으로 리팩토링됨.
"""
import ctypes
import ctypes.wintypes
import sys

from PyQt5.QtCore import Qt, QPoint, QRect

from utils.logger import log

# 리사이즈 방향 상수
_EDGE_NONE = 0
_EDGE_LEFT = 1
_EDGE_RIGHT = 2
_EDGE_TOP = 4
_EDGE_BOTTOM = 8

# 경계선 감지 영역 및 투명 마진 (픽셀)
_TRANSPARENT_MARGIN = 3
_EDGE_MARGIN = 6

# Windows Hit-Test 상수 (WM_NCHITTEST 반환값)
_HTNOWHERE = 0
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17

# Edge → HitTest 매핑
_EDGE_TO_HT = {
    _EDGE_LEFT: _HTLEFT,
    _EDGE_RIGHT: _HTRIGHT,
    _EDGE_TOP: _HTTOP,
    _EDGE_BOTTOM: _HTBOTTOM,
    _EDGE_LEFT | _EDGE_TOP: _HTTOPLEFT,
    _EDGE_RIGHT | _EDGE_TOP: _HTTOPRIGHT,
    _EDGE_LEFT | _EDGE_BOTTOM: _HTBOTTOMLEFT,
    _EDGE_RIGHT | _EDGE_BOTTOM: _HTBOTTOMRIGHT,
}

# Windows 메시지 상수
_WM_NCCALCSIZE = 0x0083
_WM_NCHITTEST = 0x0084
_WM_GETMINMAXINFO = 0x0024
_WINDOWS_NATIVE_EVENT_TYPES = (b"windows_generic_MSG", b"windows_dispatcher_MSG")


class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", ctypes.wintypes.POINT),
        ("ptMaxSize", ctypes.wintypes.POINT),
        ("ptMaxPosition", ctypes.wintypes.POINT),
        ("ptMinTrackSize", ctypes.wintypes.POINT),
        ("ptMaxTrackSize", ctypes.wintypes.POINT),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork", ctypes.wintypes.RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]


def _signed_word(value):
    return value - 65536 if value > 32767 else value


def _point_from_lparam(lparam):
    x = _signed_word(lparam & 0xFFFF)
    y = _signed_word((lparam >> 16) & 0xFFFF)
    return QPoint(x, y)


class ResizableMixin:
    """Frameless 윈도우에 Win32 API 기반 8방향 마우스 리사이징 기능을 추가하는 믹스인"""

    def _init_resizable(self, enabled=True):
        """
        리사이징 초기화. 반드시 __init__ 에서 호출해야 합니다.
        """
        self._resize_enabled = enabled
        self._use_native_resize = (sys.platform == 'win32' and enabled)
        
        if self._use_native_resize:
            hwnd = int(self.winId())
            
            # Windows 상수
            GWL_STYLE = -16
            WS_THICKFRAME = 0x00040000
            WS_CAPTION = 0x00C00000
            WS_MAXIMIZEBOX = 0x00010000
            WS_MINIMIZEBOX = 0x00020000
            WS_SYSMENU = 0x00080000
            
            # Qt.FramelessWindowHint 설정 직후, OS가 창을 리사이즈 가능하도록 인식하게 스타일 주입
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_THICKFRAME | WS_CAPTION | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU)
            
            # 프레임 변경을 OS에 알림 (SetWindowPos)
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)

    def _detect_edge(self, pos):
        """마우스 위치에서 리사이즈 방향을 감지 (투명 마진 고려)"""
        if not self._resize_enabled:
            return _EDGE_NONE

        if self.isMaximized():
            return _EDGE_NONE

        rect = self.rect()
        edge = _EDGE_NONE

        # 투명 배경(WA_TranslucentBackground)의 바깥쪽 3픽셀을 고려하여 감지 영역 확장
        effective_margin = _EDGE_MARGIN + _TRANSPARENT_MARGIN

        if pos.x() <= effective_margin:
            edge |= _EDGE_LEFT
        elif pos.x() >= rect.width() - effective_margin:
            edge |= _EDGE_RIGHT

        if pos.y() <= effective_margin:
            edge |= _EDGE_TOP
        elif pos.y() >= rect.height() - effective_margin:
            edge |= _EDGE_BOTTOM

        return edge

    def _native_msg(self, eventType, message):
        if eventType not in _WINDOWS_NATIVE_EVENT_TYPES:
            return None
        return ctypes.wintypes.MSG.from_address(int(message))

    def _handle_nccalcsize(self, msg):
        if msg.message == _WM_NCCALCSIZE and msg.wParam:
            return True, 0
        return None

    def _handle_getminmaxinfo(self, msg):
        if msg.message != _WM_GETMINMAXINFO:
            return None

        mmi = MINMAXINFO.from_address(msg.lParam)
        monitor = ctypes.windll.user32.MonitorFromWindow(msg.hWnd, 2)
        monitor_info = MONITORINFO()
        monitor_info.cbSize = ctypes.sizeof(MONITORINFO)
        ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(monitor_info))

        self._apply_maximized_work_area(mmi, monitor_info)
        self._apply_min_track_size(mmi)
        return True, 0

    def _apply_maximized_work_area(self, mmi, monitor_info):
        mmi.ptMaxSize.x = monitor_info.rcWork.right - monitor_info.rcWork.left
        mmi.ptMaxSize.y = monitor_info.rcWork.bottom - monitor_info.rcWork.top
        mmi.ptMaxPosition.x = monitor_info.rcWork.left - monitor_info.rcMonitor.left
        mmi.ptMaxPosition.y = monitor_info.rcWork.top - monitor_info.rcMonitor.top

    def _apply_min_track_size(self, mmi):
        min_size = self.minimumSize()
        min_w = min_size.width()
        min_h = min_size.height()

        hint = self.minimumSizeHint()
        if min_w <= 0:
            min_w = hint.width()
        if min_h <= 0:
            min_h = hint.height()

        if min_w <= 0:
            min_w = 400
        if min_h <= 0:
            min_h = 300

        mmi.ptMinTrackSize.x = min_w
        mmi.ptMinTrackSize.y = min_h

    def _handle_nchittest(self, msg):
        if msg.message != _WM_NCHITTEST or self.isMaximized():
            return None

        global_pos = _point_from_lparam(msg.lParam)
        local_pos = self.mapFromGlobal(global_pos)
        edge = self._detect_edge(local_pos)
        if edge in _EDGE_TO_HT:
            return True, _EDGE_TO_HT[edge]
        return None

    def nativeEvent(self, eventType, message):
        """
        Windows 네이티브 이벤트 처리.
        WM_NCCALCSIZE: OS의 기본 프레임/타이틀바 렌더링 차단 (최대화 시에도 반드시 처리)
        WM_GETMINMAXINFO: 최대화 시 작업 표시줄 덮음 방지 및 최소 크기 지정
        WM_NCHITTEST: 커스텀 경계선 영역에서의 리사이즈 커서 및 동작 처리
        """
        if self._use_native_resize:
            try:
                msg = self._native_msg(eventType, message)
                if msg is not None:
                    for handler in (
                        self._handle_nccalcsize,
                        self._handle_getminmaxinfo,
                        self._handle_nchittest,
                    ):
                        result = handler(msg)
                        if result is not None:
                            return result
            except Exception as e:
                log.debug(f"Native resize event handling failed: {e}")

        return super().nativeEvent(eventType, message)

    # ── 기존 Qt 마우스 이벤트 폴백 유지 (더 이상 Win32에서는 사용되지 않음) ──
    # 다른 클래스(BaseDialog 등)에서 이 메서드들을 호출할 수 있으므로 시그니처와 기본 반환값만 남김

    def resizable_mouse_press(self, event):
        return False

    def resizable_mouse_move(self, event):
        return False

    def resizable_mouse_release(self, event):
        return False

    def is_on_resize_edge(self, pos):
        return self._detect_edge(pos) != _EDGE_NONE
