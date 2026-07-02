import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.main_window.view_state import (
    hide_task_list_if_empty,
    set_url_entry_enabled,
    show_task_list,
)


class FakeVisibilityWidget:
    def __init__(self, hidden=False):
        self.hidden = hidden
        self.show_calls = 0
        self.hide_calls = 0

    def isHidden(self):
        return self.hidden

    def show(self):
        self.hidden = False
        self.show_calls += 1

    def hide(self):
        self.hidden = True
        self.hide_calls += 1


class FakeEnabledWidget:
    def __init__(self):
        self.enabled = None

    def setEnabled(self, enabled):
        self.enabled = enabled


class MainWindowViewStateTests(unittest.TestCase):
    def test_show_task_list_reveals_hidden_list_and_hides_empty_label(self):
        scroll_area = FakeVisibilityWidget(hidden=True)
        empty_label = FakeVisibilityWidget(hidden=False)

        changed = show_task_list(scroll_area, empty_label)

        self.assertTrue(changed)
        self.assertFalse(scroll_area.hidden)
        self.assertEqual(scroll_area.show_calls, 1)
        self.assertEqual(empty_label.hide_calls, 1)

    def test_show_task_list_noops_when_already_visible(self):
        scroll_area = FakeVisibilityWidget(hidden=False)
        empty_label = FakeVisibilityWidget(hidden=False)

        changed = show_task_list(scroll_area, empty_label)

        self.assertFalse(changed)
        self.assertEqual(scroll_area.show_calls, 0)
        self.assertEqual(empty_label.hide_calls, 0)

    def test_hide_task_list_if_empty_shows_empty_state(self):
        scroll_area = FakeVisibilityWidget(hidden=False)
        empty_label = FakeVisibilityWidget(hidden=True)

        changed = hide_task_list_if_empty({}, scroll_area, empty_label)

        self.assertTrue(changed)
        self.assertTrue(scroll_area.hidden)
        self.assertFalse(empty_label.hidden)
        self.assertEqual(scroll_area.hide_calls, 1)
        self.assertEqual(empty_label.show_calls, 1)

    def test_hide_task_list_if_empty_keeps_visible_when_widgets_remain(self):
        scroll_area = FakeVisibilityWidget(hidden=False)
        empty_label = FakeVisibilityWidget(hidden=True)

        changed = hide_task_list_if_empty({1: object()}, scroll_area, empty_label)

        self.assertFalse(changed)
        self.assertEqual(scroll_area.hide_calls, 0)
        self.assertEqual(empty_label.show_calls, 0)

    def test_set_url_entry_enabled_applies_same_state_to_both_controls(self):
        url_input = FakeEnabledWidget()
        download_button = FakeEnabledWidget()

        set_url_entry_enabled(url_input, download_button, False)

        self.assertFalse(url_input.enabled)
        self.assertFalse(download_button.enabled)


if __name__ == "__main__":
    unittest.main()