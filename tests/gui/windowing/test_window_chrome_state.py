import os
import sys
import unittest

from PyQt5.QtCore import QPoint

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.main_window.chrome_state import (
    MAXIMIZE_ICON_NAME,
    RESTORE_ICON_NAME,
    build_window_chrome_state,
    chrome_state_after_window_change,
    has_window_drag_started,
    should_continue_window_drag,
    should_start_window_drag,
    should_toggle_maximize_from_double_click,
)


class WindowChromeStateTests(unittest.TestCase):
    def test_build_window_chrome_state_for_maximized_window(self):
        state = build_window_chrome_state(True, "normal", "maximized")

        self.assertTrue(state.is_maximized)
        self.assertEqual(state.central_style, "maximized")
        self.assertEqual(state.maximize_icon_name, RESTORE_ICON_NAME)

    def test_build_window_chrome_state_for_normal_window(self):
        state = build_window_chrome_state(False, "normal", "maximized")

        self.assertFalse(state.is_maximized)
        self.assertEqual(state.central_style, "normal")
        self.assertEqual(state.maximize_icon_name, MAXIMIZE_ICON_NAME)

    def test_should_start_window_drag_requires_title_bar_left_click(self):
        self.assertTrue(should_start_window_drag("left", "left", True))
        self.assertFalse(should_start_window_drag("left", "left", False))
        self.assertFalse(should_start_window_drag("right", "left", True))

    def test_should_continue_window_drag_requires_previous_position_and_left_button(self):
        self.assertTrue(should_continue_window_drag("old-pos", "left", "left"))
        self.assertFalse(should_continue_window_drag(None, "left", "left"))
        self.assertFalse(should_continue_window_drag("old-pos", "right", "left"))

    def test_has_window_drag_started_uses_movement_threshold(self):
        self.assertFalse(has_window_drag_started(None, QPoint(0, 0), 4))
        self.assertFalse(has_window_drag_started(QPoint(10, 10), QPoint(12, 11), 4))
        self.assertTrue(has_window_drag_started(QPoint(10, 10), QPoint(13, 11), 4))

    def test_should_toggle_maximize_from_title_bar_double_click(self):
        self.assertTrue(
            should_toggle_maximize_from_double_click("left", "left", 40, 30)
        )
        self.assertFalse(
            should_toggle_maximize_from_double_click("right", "left", 20, 30)
        )
        self.assertFalse(
            should_toggle_maximize_from_double_click("left", "left", 41, 30)
        )

    def test_chrome_state_after_window_change_returns_needed_transition(self):
        self.assertTrue(chrome_state_after_window_change(True, False, False))
        self.assertFalse(chrome_state_after_window_change(False, False, True))
        self.assertIsNone(chrome_state_after_window_change(True, False, True))
        self.assertIsNone(chrome_state_after_window_change(False, True, True))


if __name__ == "__main__":
    unittest.main()
