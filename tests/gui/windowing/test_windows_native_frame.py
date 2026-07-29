import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import QSize

from gui.windowing.windows_custom_frame_mixin import (
    WindowsCustomFrameMixin,
    native_point_from_lparam,
)
from gui.windowing.windows_native_frame import (
    HTBOTTOM,
    HTBOTTOMLEFT,
    HTBOTTOMRIGHT,
    HTCLIENT,
    HTLEFT,
    HTRIGHT,
    HTTOP,
    HTTOPLEFT,
    HTTOPRIGHT,
    RECT,
    WS_CAPTION,
    WS_MAXIMIZEBOX,
    WS_MINIMIZEBOX,
    WS_POPUP,
    WS_SYSMENU,
    WS_THICKFRAME,
    custom_frame_style,
    inset_maximized_client_rect,
    maximized_outer_bounds,
    native_hit_test_for_rect,
)


class FakeCustomFrame(WindowsCustomFrameMixin):
    def __init__(self, ratio, minimum=None, minimum_hint=None):
        self._ratio = ratio
        self._minimum = QSize() if minimum is None else minimum
        self._minimum_hint = QSize() if minimum_hint is None else minimum_hint
        self._windows_content_margin = 5

    def devicePixelRatioF(self):
        return self._ratio

    def minimumSize(self):
        return self._minimum

    def minimumSizeHint(self):
        return self._minimum_hint


class WindowsNativeFrameTests(unittest.TestCase):
    def test_style_matches_qt_frameless_native_capabilities(self):
        style = custom_frame_style(WS_POPUP)

        self.assertFalse(style & WS_POPUP)
        self.assertTrue(style & WS_THICKFRAME)
        self.assertTrue(style & WS_CAPTION)
        self.assertTrue(style & WS_MINIMIZEBOX)
        self.assertTrue(style & WS_MAXIMIZEBOX)
        self.assertTrue(style & WS_SYSMENU)

    def test_style_update_is_idempotent(self):
        style = custom_frame_style(WS_POPUP)
        self.assertEqual(custom_frame_style(style), style)

    def test_hit_test_uses_all_native_edges_and_corners(self):
        rect = RECT(100, 200, 500, 600)
        points = {
            (101, 400): HTLEFT,
            (499, 400): HTRIGHT,
            (300, 201): HTTOP,
            (300, 599): HTBOTTOM,
            (101, 201): HTTOPLEFT,
            (499, 201): HTTOPRIGHT,
            (101, 599): HTBOTTOMLEFT,
            (499, 599): HTBOTTOMRIGHT,
            (300, 400): HTCLIENT,
        }

        for point, expected in points.items():
            with self.subTest(point=point):
                self.assertEqual(
                    native_hit_test_for_rect(*point, rect, 8, 8),
                    expected,
                )

    def test_maximized_outer_bounds_overhang_by_invisible_border(self):
        monitor = RECT(0, 0, 2560, 1440)
        work = RECT(0, 0, 2560, 1400)

        self.assertEqual(
            maximized_outer_bounds(monitor, work, 8, 8),
            (-8, -8, 2576, 1416),
        )

    def test_maximized_client_is_inset_back_to_work_area(self):
        rect = RECT(-8, -8, 2568, 1408)
        inset_maximized_client_rect(rect, 8, 8)

        self.assertEqual(
            (rect.left, rect.top, rect.right, rect.bottom),
            (0, 0, 2560, 1400),
        )

    def test_native_point_supports_negative_monitor_coordinates(self):
        packed = ((34 & 0xFFFF) << 16) | (-12 & 0xFFFF)
        self.assertEqual(native_point_from_lparam(packed), (-12, 34))

    def test_qt_content_margin_uses_qt_device_pixel_ratio(self):
        expected_margins = ((1.0, 5), (1.25, 6), (1.5, 8), (2.0, 10))

        for ratio, expected in expected_margins:
            with self.subTest(ratio=ratio):
                frame = FakeCustomFrame(ratio)
                self.assertEqual(frame._physical_content_margin(None), expected)

    def test_minimum_track_size_uses_effective_qt_minimum_and_ratio(self):
        compact = FakeCustomFrame(
            1.0,
            minimum=QSize(0, 0),
            minimum_hint=QSize(800, 494),
        )
        scaled = FakeCustomFrame(
            1.5,
            minimum=QSize(0, 0),
            minimum_hint=QSize(800, 494),
        )
        explicit = FakeCustomFrame(
            1.0,
            minimum=QSize(805, 500),
            minimum_hint=QSize(800, 494),
        )

        self.assertEqual(compact._physical_minimum_track_size(), (800, 494))
        self.assertEqual(scaled._physical_minimum_track_size(), (1200, 741))
        self.assertEqual(explicit._physical_minimum_track_size(), (805, 500))


if __name__ == "__main__":
    unittest.main()
