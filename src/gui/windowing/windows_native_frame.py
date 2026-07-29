"""Low-level Win32 helpers for a visually frameless, natively resizable window."""

import ctypes
import ctypes.wintypes
import sys

GWL_STYLE = -16

WS_POPUP = 0x80000000
WS_THICKFRAME = 0x00040000
WS_MINIMIZEBOX = 0x00020000
WS_MAXIMIZEBOX = 0x00010000
WS_SYSMENU = 0x00080000
WS_CAPTION = 0x00C00000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020

WM_GETMINMAXINFO = 0x0024
WM_NCCALCSIZE = 0x0083
WM_NCHITTEST = 0x0084
WM_DWMCOMPOSITIONCHANGED = 0x031E
WVR_REDRAW = 0x0300

HTCLIENT = 1
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

MONITOR_DEFAULTTONEAREST = 2
SM_CXSIZEFRAME = 32
SM_CYSIZEFRAME = 33
SM_CXPADDEDBORDER = 92


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MARGINS(ctypes.Structure):
    _fields_ = [
        ("cxLeftWidth", ctypes.c_int),
        ("cxRightWidth", ctypes.c_int),
        ("cyTopHeight", ctypes.c_int),
        ("cyBottomHeight", ctypes.c_int),
    ]


class WINDOWPOS(ctypes.Structure):
    _fields_ = [
        ("hwnd", ctypes.wintypes.HWND),
        ("hwndInsertAfter", ctypes.wintypes.HWND),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("cx", ctypes.c_int),
        ("cy", ctypes.c_int),
        ("flags", ctypes.c_uint),
    ]


class NCCALCSIZE_PARAMS(ctypes.Structure):
    _fields_ = [
        ("rgrc", RECT * 3),
        ("lppos", ctypes.POINTER(WINDOWPOS)),
    ]


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
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]


def custom_frame_style(style: int) -> int:
    """Return the native flags used by modern Qt frameless Windows windows."""
    unsigned_style = ctypes.c_uint32(style).value
    return (
        (unsigned_style & ~WS_POPUP)
        | WS_THICKFRAME
        | WS_CAPTION
        | WS_MINIMIZEBOX
        | WS_MAXIMIZEBOX
        | WS_SYSMENU
    )


def _native_hwnd(hwnd):
    """Normalize either an integer or an existing ctypes HWND value."""
    value = getattr(hwnd, "value", hwnd)
    return ctypes.wintypes.HWND(value)


def _user32():
    user32 = ctypes.windll.user32
    user32.GetWindowLongW.argtypes = [ctypes.wintypes.HWND, ctypes.c_int]
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.SetWindowLongW.argtypes = [
        ctypes.wintypes.HWND,
        ctypes.c_int,
        ctypes.c_long,
    ]
    user32.SetWindowLongW.restype = ctypes.c_long
    user32.SetWindowPos.argtypes = [
        ctypes.wintypes.HWND,
        ctypes.wintypes.HWND,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_int,
        ctypes.c_uint,
    ]
    user32.SetWindowPos.restype = ctypes.wintypes.BOOL
    user32.GetWindowRect.argtypes = [ctypes.wintypes.HWND, ctypes.POINTER(RECT)]
    user32.GetWindowRect.restype = ctypes.wintypes.BOOL
    user32.IsZoomed.argtypes = [ctypes.wintypes.HWND]
    user32.IsZoomed.restype = ctypes.wintypes.BOOL
    user32.MonitorFromWindow.argtypes = [ctypes.wintypes.HWND, ctypes.c_uint]
    user32.MonitorFromWindow.restype = ctypes.wintypes.HMONITOR
    user32.GetMonitorInfoW.argtypes = [
        ctypes.wintypes.HMONITOR,
        ctypes.POINTER(MONITORINFO),
    ]
    user32.GetMonitorInfoW.restype = ctypes.wintypes.BOOL
    return user32


def _dwmapi():
    dwmapi = ctypes.windll.dwmapi
    dwmapi.DwmExtendFrameIntoClientArea.argtypes = [
        ctypes.wintypes.HWND,
        ctypes.POINTER(MARGINS),
    ]
    dwmapi.DwmExtendFrameIntoClientArea.restype = ctypes.c_long
    return dwmapi


def extend_dwm_frame(hwnd) -> bool:
    """Ask DWM for the standard shadow and invisible resize-frame treatment."""
    if sys.platform != "win32":
        return False
    margins = MARGINS(-1, -1, -1, -1)
    return _dwmapi().DwmExtendFrameIntoClientArea(
        _native_hwnd(hwnd),
        ctypes.byref(margins),
    ) == 0


def enable_windows_custom_frame(window) -> bool:
    """Install native capabilities while leaving all frame drawing to Qt."""
    if sys.platform != "win32":
        return False

    hwnd = ctypes.wintypes.HWND(int(window.winId()))
    user32 = _user32()
    current_style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    user32.SetWindowLongW(
        hwnd,
        GWL_STYLE,
        ctypes.c_long(custom_frame_style(current_style)).value,
    )
    extend_dwm_frame(hwnd)
    user32.SetWindowPos(
        hwnd,
        None,
        0,
        0,
        0,
        0,
        SWP_NOMOVE
        | SWP_NOSIZE
        | SWP_NOZORDER
        | SWP_NOACTIVATE
        | SWP_FRAMECHANGED,
    )
    return True


def window_rect(hwnd):
    """Return the native window rectangle in physical screen pixels."""
    if sys.platform != "win32":
        return None
    rect = RECT()
    if not _user32().GetWindowRect(_native_hwnd(hwnd), ctypes.byref(rect)):
        return None
    return rect


def native_window_dpi(hwnd) -> int:
    """Return the DPI currently assigned to a native window."""
    if sys.platform != "win32":
        return 96
    user32 = _user32()
    get_dpi_for_window = getattr(user32, "GetDpiForWindow", None)
    if get_dpi_for_window is None:
        return 96
    get_dpi_for_window.argtypes = [ctypes.wintypes.HWND]
    get_dpi_for_window.restype = ctypes.c_uint
    return int(get_dpi_for_window(_native_hwnd(hwnd))) or 96


def windows_resize_border(hwnd) -> tuple[int, int]:
    """Return native horizontal and vertical resize thickness in physical pixels."""
    if sys.platform != "win32":
        return 0, 0

    user32 = _user32()
    dpi = native_window_dpi(hwnd)
    get_metric_for_dpi = getattr(user32, "GetSystemMetricsForDpi", None)
    if get_metric_for_dpi is not None:
        get_metric_for_dpi.argtypes = [ctypes.c_int, ctypes.c_uint]
        get_metric_for_dpi.restype = ctypes.c_int
        metric = lambda name: int(get_metric_for_dpi(name, dpi))
    else:
        user32.GetSystemMetrics.argtypes = [ctypes.c_int]
        user32.GetSystemMetrics.restype = ctypes.c_int
        metric = lambda name: int(user32.GetSystemMetrics(name))

    padded = metric(SM_CXPADDEDBORDER)
    return metric(SM_CXSIZEFRAME) + padded, metric(SM_CYSIZEFRAME) + padded


def native_hit_test_for_rect(
    x: int,
    y: int,
    rect: RECT,
    horizontal_border: int,
    vertical_border: int,
) -> int:
    """Return a Win32 resize hit code for a physical point in a window rectangle."""
    if horizontal_border <= 0 or vertical_border <= 0:
        return HTCLIENT

    left = rect.left <= x < rect.left + horizontal_border
    right = rect.right - horizontal_border < x <= rect.right
    top = rect.top <= y < rect.top + vertical_border
    bottom = rect.bottom - vertical_border < y <= rect.bottom

    if left:
        if top:
            return HTTOPLEFT
        if bottom:
            return HTBOTTOMLEFT
        return HTLEFT
    if right:
        if top:
            return HTTOPRIGHT
        if bottom:
            return HTBOTTOMRIGHT
        return HTRIGHT
    if top:
        return HTTOP
    if bottom:
        return HTBOTTOM
    return HTCLIENT


def inset_maximized_client_rect(rect: RECT, border_x: int, border_y: int) -> None:
    """Keep maximized content inside the work area while the outer frame overhangs."""
    rect.left += border_x
    rect.right -= border_x
    rect.top += border_y
    rect.bottom -= border_y


def maximized_outer_bounds(
    monitor_rect: RECT,
    work_rect: RECT,
    border_x: int,
    border_y: int,
) -> tuple[int, int, int, int]:
    """Return max position and size including the invisible frame overhang."""
    return (
        work_rect.left - monitor_rect.left - border_x,
        work_rect.top - monitor_rect.top - border_y,
        work_rect.right - work_rect.left + border_x * 2,
        work_rect.bottom - work_rect.top + border_y * 2,
    )


def monitor_info_for_window(hwnd):
    """Return monitor and work-area rectangles for the nearest monitor."""
    if sys.platform != "win32":
        return None
    user32 = _user32()
    monitor = user32.MonitorFromWindow(
        _native_hwnd(hwnd), MONITOR_DEFAULTTONEAREST
    )
    info = MONITORINFO()
    info.cbSize = ctypes.sizeof(MONITORINFO)
    if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
        return None
    return info


def is_native_window_maximized(hwnd) -> bool:
    if sys.platform != "win32":
        return False
    return bool(_user32().IsZoomed(_native_hwnd(hwnd)))
