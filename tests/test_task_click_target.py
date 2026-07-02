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

from gui.tasks.task_click_target import is_click_on_child_type


class FakeButton:
    def __init__(self, parent=None):
        self._parent = parent

    def parent(self):
        return self._parent


class FakeWidget:
    def __init__(self, parent=None):
        self._parent = parent

    def parent(self):
        return self._parent


class TaskClickTargetTests(unittest.TestCase):
    def test_detects_direct_button_click(self):
        root = FakeWidget()
        button = FakeButton(root)

        self.assertTrue(is_click_on_child_type(button, root, FakeButton))

    def test_detects_child_inside_button(self):
        root = FakeWidget()
        button = FakeButton(root)
        icon_label = FakeWidget(button)

        self.assertTrue(is_click_on_child_type(icon_label, root, FakeButton))

    def test_stops_before_root_widget(self):
        root = FakeButton()
        child = FakeWidget(root)

        self.assertFalse(is_click_on_child_type(child, root, FakeButton))

    def test_returns_false_for_unrelated_or_empty_clicks(self):
        root = FakeWidget()

        self.assertFalse(is_click_on_child_type(None, root, FakeButton))
        self.assertFalse(is_click_on_child_type(FakeWidget(root), root, FakeButton))


if __name__ == "__main__":
    unittest.main()
