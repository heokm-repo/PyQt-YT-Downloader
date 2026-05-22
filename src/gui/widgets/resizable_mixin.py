"""
ResizableMixin — Frameless 윈도우의 8방향 마우스 리사이징 믹스인

순수 Qt 이벤트 방식이 아닌, Win32 API와 nativeEvent를 활용한 방식으로 리팩토링됨.
"""
import sys
from PyQt5.QtCore import Qt, QPoint, QRect

# 리사이즈 방향 상수
_EDGE_NONE   = 0
_EDGE_LEFT   = 1
_EDGE_RIGHT  = 2
_EDGE_TOP    = 4
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
    _EDGE_LEFT:                     _HTLEFT,
    _EDGE_RIGHT:                    _HTRIGHT,
    _EDGE_TOP:                      _HTTOP,
    _EDGE_BOTTOM:                   _HTBOTTOM,
    _EDGE_LEFT  | _EDGE_TOP:        _HTTOPLEFT,
    _EDGE_RIGHT | _EDGE_TOP:        _HTTOPRIGHT,
    _EDGE_LEFT  | _EDGE_BOTTOM:     _HTBOTTOMLEFT,
    _EDGE_RIGHT | _EDGE_BOTTOM:     _HTBOTTOMRIGHT,
}

# Windows 메시지 상수
_WM_NCCALCSIZE = 0x0083
_WM_NCHITTEST = 0x0084


class ResizableMixin:
    """Frameless 윈도우에 Win32 API 기반 8방향 마우스 리사이징 기능을 추가하는 믹스인"""

    def _init_resizable(self, enabled=True):
        """
        리사이징 초기화. 반드시 __init__ 에서 호출해야 합니다.
        """
        self._resize_enabled = enabled
        self._use_native_resize = (sys.platform == 'win32' and enabled)
        
        if self._use_native_resize:
            import ctypes
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

    def nativeEvent(self, eventType, message):
        """
        Windows 네이티브 이벤트 처리.
        WM_NCCALCSIZE: OS의 기본 프레임/타이틀바 렌더링 차단 (최대화 시에도 반드시 처리)
        WM_NCHITTEST: 커스텀 경계선 영역에서의 리사이즈 커서 및 동작 처리
        """
        if self._use_native_resize:
            try:
                if eventType == b"windows_generic_MSG" or eventType == b"windows_dispatcher_MSG":
                    import ctypes
                    import ctypes.wintypes

                    msg = ctypes.wintypes.MSG.from_address(int(message))

                    # 1. WM_NCCALCSIZE: 항상 처리하여 OS 기본 프레임 렌더링 차단
                    if msg.message == _WM_NCCALCSIZE:
                        if msg.wParam:
                            # 프레임이 제거된 전체 영역을 클라이언트 영역으로 사용
                            return True, 0

                    # 1-1. WM_GETMINMAXINFO: 최대화 시 작업 표시줄 덮음 방지 및 최소/최대 크기 지정
                    elif msg.message == 0x0024:  # WM_GETMINMAXINFO
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
                                ('cbSize', ctypes.wintypes.DWORD),
                                ('rcMonitor', ctypes.wintypes.RECT),
                                ('rcWork', ctypes.wintypes.RECT),
                                ('dwFlags', ctypes.wintypes.DWORD),
                            ]
                        mmi = MINMAXINFO.from_address(msg.lParam)
                        # 현재 창이 띄워질 모니터 찾기
                        monitor = ctypes.windll.user32.MonitorFromWindow(msg.hWnd, 2)
                        mi = MONITORINFO()
                        mi.cbSize = ctypes.sizeof(MONITORINFO)
                        ctypes.windll.user32.GetMonitorInfoW(monitor, ctypes.byref(mi))
                        
                        # 최대화 크기를 모니터의 작업 영역 크기로 제한
                        mmi.ptMaxSize.x = mi.rcWork.right - mi.rcWork.left
                        mmi.ptMaxSize.y = mi.rcWork.bottom - mi.rcWork.top
                        
                        # 최대화 시 위치를 모니터 상대 좌표로 보정
                        mmi.ptMaxPosition.x = mi.rcWork.left - mi.rcMonitor.left
                        mmi.ptMaxPosition.y = mi.rcWork.top - mi.rcMonitor.top
                        
                        # 바텀업 최소 크기 보장 (minimumSize 또는 minimumSizeHint 적용)
                        min_size = self.minimumSize()
                        min_w = min_size.width()
                        min_h = min_size.height()
                        
                        hint = self.minimumSizeHint()
                        if min_w <= 0:
                            min_w = hint.width()
                        if min_h <= 0:
                            min_h = hint.height()
                            
                        # 디폴트 최소 크기 안전장치
                        if min_w <= 0:
                            min_w = 400
                        if min_h <= 0:
                            min_h = 300
                            
                        mmi.ptMinTrackSize.x = min_w
                        mmi.ptMinTrackSize.y = min_h
                        return True, 0

                    # 2. WM_NCHITTEST: 최대화 상태가 아닐 때만 리사이즈 영역 판별
                    elif msg.message == _WM_NCHITTEST and not self.isMaximized():
                        # lParam에서 화면 좌표(글로벌 좌표) 추출 (signed 16-bit)
                        x = msg.lParam & 0xFFFF
                        y = (msg.lParam >> 16) & 0xFFFF
                        
                        # 멀티 모니터 환경의 음수 좌표 대응
                        if x > 32767: x -= 65536
                        if y > 32767: y -= 65536

                        # 글로벌 좌표를 윈도우 내부 로컬 좌표로 변환
                        pos = self.mapFromGlobal(QPoint(x, y))
                        
                        # 투명 마진을 고려한 경계선 판별
                        edge = self._detect_edge(pos)

                        if edge in _EDGE_TO_HT:
                            return True, _EDGE_TO_HT[edge]
                            
                    # 3. 리사이즈 또는 창 이동 종료 시 로그 기록
                    elif msg.message == 0x0232: # WM_EXITSIZEMOVE
                        try:
                            from utils.logger import log
                            name = getattr(self, '_window_name', self.__class__.__name__)
                            geo = self.geometry()
                            log.info(f"창 크기/위치 변경 완료 ({name}): {geo.width()}x{geo.height()} 위치({geo.x()}, {geo.y()})")
                        except Exception:
                            pass
            except Exception:
                pass

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
