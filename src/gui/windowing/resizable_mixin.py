"""ResizableMixin for eight-way mouse resizing on frameless windows, implemented with Win32 API and nativeEvent."""
import ctypes
import ctypes.wintypes
import sys

from PyQt5.QtCore import Qt, QPoint, QRect

from utils.logger import log

# Resize direction constants.
_EDGE_NONE = 0
_EDGE_LEFT = 1
_EDGE_RIGHT = 2
_EDGE_TOP = 4
_EDGE_BOTTOM = 8

# Border detection area and transparent margin in pixels.
_TRANSPARENT_MARGIN = 3
_EDGE_MARGIN = 6

# Windows hit-test constants returned by WM_NCHITTEST.
_HTNOWHERE = 0
_HTLEFT = 10
_HTRIGHT = 11
_HTTOP = 12
_HTTOPLEFT = 13
_HTTOPRIGHT = 14
_HTBOTTOM = 15
_HTBOTTOMLEFT = 16
_HTBOTTOMRIGHT = 17

# Edge-to-hit-test mapping.
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

# Windows message constants.
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
    """Mixin that adds Win32 API based eight-way mouse resizing to frameless windows."""

    def _init_resizable(self, enabled=True):
        """Initialize resizing; call this from __init__."""
        self._resize_enabled = enabled
        self._use_native_resize = (sys.platform == 'win32' and enabled)

        if self._use_native_resize:
            hwnd = int(self.winId())

            # Windows constants.
            GWL_STYLE = -16
            WS_THICKFRAME = 0x00040000
            WS_CAPTION = 0x00C00000
            WS_MAXIMIZEBOX = 0x00010000
            WS_MINIMIZEBOX = 0x00020000
            WS_SYSMENU = 0x00080000

            # After Qt.FramelessWindowHint, inject styles so the OS treats the window as resizable.
            user32 = ctypes.windll.user32
            style = user32.GetWindowLongW(hwnd, GWL_STYLE)
            user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_THICKFRAME | WS_CAPTION | WS_MAXIMIZEBOX | WS_MINIMIZEBOX | WS_SYSMENU)

            # Notify the OS that the frame changed.
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE = 0x0002
            SWP_NOSIZE = 0x0001
            SWP_NOZORDER = 0x0004
            user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED)

    def _detect_edge(self, pos):
        """Detect the resize edge at the mouse position, including transparent margins."""
        if not self._resize_enabled:
            return _EDGE_NONE

        if self.isMaximized():
            return _EDGE_NONE

        rect = self.rect()
        edge = _EDGE_NONE

        # Expand detection for the outer 3 px of the translucent background.
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
        Handle Windows native events.

        WM_NCCALCSIZE blocks the default OS frame and title bar. WM_GETMINMAXINFO prevents maximized windows from covering the taskbar and applies minimum sizes. WM_NCHITTEST handles resize cursors and behavior on custom borders.
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

    # -- Existing Qt mouse-event fallback, no longer used on Win32 ---------
    # Other classes may call these methods, so keep their signatures and defaults.

    def resizable_mouse_press(self, event):
        return False

    def resizable_mouse_move(self, event):
        return False

    def resizable_mouse_release(self, event):
        return False

    def is_on_resize_edge(self, pos):
        return self._detect_edge(pos) != _EDGE_NONE
