"""PyQt native-event adapter for custom frameless Windows windows."""

import ctypes
import ctypes.wintypes
import logging
import math
import sys

from gui.windowing.windows_native_frame import (
    HTCLIENT,
    MINMAXINFO,
    NCCALCSIZE_PARAMS,
    WM_DWMCOMPOSITIONCHANGED,
    WM_GETMINMAXINFO,
    WM_NCCALCSIZE,
    WM_NCHITTEST,
    WVR_REDRAW,
    enable_windows_custom_frame,
    extend_dwm_frame,
    inset_maximized_client_rect,
    is_native_window_maximized,
    maximized_outer_bounds,
    monitor_info_for_window,
    native_hit_test_for_rect,
    window_rect,
    windows_resize_border,
)

logger = logging.getLogger(__name__)
_WINDOWS_NATIVE_EVENT_TYPES = (b"windows_generic_MSG", b"windows_dispatcher_MSG")
# Preserve the legacy dialog hit area: 6 px edge plus 3 px translucent margin.
DEFAULT_RESIZE_CONTENT_MARGIN = 9


def _signed_word(value: int) -> int:
    return value - 65536 if value > 32767 else value


def native_point_from_lparam(lparam: int) -> tuple[int, int]:
    """Decode physical screen coordinates, including negative monitor positions."""
    return (
        _signed_word(lparam & 0xFFFF),
        _signed_word((lparam >> 16) & 0xFFFF),
    )


class WindowsCustomFrameMixin:
    """Hide native chrome while retaining the Windows-managed outer resize frame."""

    def _init_windows_custom_frame(
        self,
        enabled: bool = True,
        content_margin: int = DEFAULT_RESIZE_CONTENT_MARGIN,
    ) -> None:
        self._windows_content_margin = max(0, int(content_margin))
        self._windows_custom_frame_enabled = bool(enabled and sys.platform == "win32")
        if self._windows_custom_frame_enabled:
            self._windows_custom_frame_enabled = enable_windows_custom_frame(self)

    def _native_message(self, event_type, message):
        if event_type not in _WINDOWS_NATIVE_EVENT_TYPES:
            return None
        return ctypes.wintypes.MSG.from_address(int(message))

    def _qt_device_pixel_ratio(self) -> float:
        ratio = float(self.devicePixelRatioF())
        return ratio if ratio > 0 else 1.0

    def _physical_content_margin(self, _hwnd) -> int:
        return round(self._windows_content_margin * self._qt_device_pixel_ratio())

    def _physical_minimum_track_size(self) -> tuple[int, int]:
        minimum = self.minimumSize().expandedTo(self.minimumSizeHint())
        ratio = self._qt_device_pixel_ratio()
        return (
            math.ceil(max(0, minimum.width()) * ratio),
            math.ceil(max(0, minimum.height()) * ratio),
        )

    def _handle_custom_nccalcsize(self, msg):
        if msg.message != WM_NCCALCSIZE or not msg.wParam:
            return None

        if is_native_window_maximized(msg.hWnd):
            params = NCCALCSIZE_PARAMS.from_address(msg.lParam)
            border_x, border_y = windows_resize_border(msg.hWnd)
            inset_maximized_client_rect(params.rgrc[0], border_x, border_y)
        return True, WVR_REDRAW

    def _handle_custom_minmaxinfo(self, msg):
        if msg.message != WM_GETMINMAXINFO:
            return None

        monitor = monitor_info_for_window(msg.hWnd)
        if monitor is None:
            return None

        border_x, border_y = windows_resize_border(msg.hWnd)
        x, y, width, height = maximized_outer_bounds(
            monitor.rcMonitor,
            monitor.rcWork,
            border_x,
            border_y,
        )
        minmax = MINMAXINFO.from_address(msg.lParam)
        minmax.ptMaxPosition.x = x
        minmax.ptMaxPosition.y = y
        minmax.ptMaxSize.x = width
        minmax.ptMaxSize.y = height

        min_width, min_height = self._physical_minimum_track_size()
        minmax.ptMinTrackSize.x = min_width
        minmax.ptMinTrackSize.y = min_height
        return True, 0

    def _handle_custom_nchittest(self, msg):
        if msg.message != WM_NCHITTEST:
            return None
        if is_native_window_maximized(msg.hWnd):
            return True, HTCLIENT

        rect = window_rect(msg.hWnd)
        if rect is None:
            return None
        x, y = native_point_from_lparam(msg.lParam)
        content_margin = self._physical_content_margin(msg.hWnd)
        return True, native_hit_test_for_rect(
            x,
            y,
            rect,
            content_margin,
            content_margin,
        )

    def nativeEvent(self, eventType, message):
        if getattr(self, "_windows_custom_frame_enabled", False):
            try:
                msg = self._native_message(eventType, message)
                if msg is not None:
                    for handler in (
                        self._handle_custom_nccalcsize,
                        self._handle_custom_minmaxinfo,
                        self._handle_custom_nchittest,
                    ):
                        result = handler(msg)
                        if result is not None:
                            return result

                    if msg.message == WM_DWMCOMPOSITIONCHANGED:
                        extend_dwm_frame(msg.hWnd)
            except Exception as error:
                logger.debug("Windows custom-frame event handling failed: %s", error)
        return super().nativeEvent(eventType, message)
