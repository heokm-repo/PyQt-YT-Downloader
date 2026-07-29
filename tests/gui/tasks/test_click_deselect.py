import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.main_window.click_deselect import is_widget_or_parent_in, should_clear_selection_for_click


class FakeWidget:
    def __init__(self, parent=None, child=None):
        self._parent = parent
        self._child = child

    def parent(self):
        return self._parent

    def childAt(self, pos):
        return self._child


class ClickDeselectTests(unittest.TestCase):
    def test_is_widget_or_parent_in_detects_parent_chain(self):
        task_widget = FakeWidget()
        child = FakeWidget(parent=task_widget)

        self.assertTrue(is_widget_or_parent_in(child, [task_widget]))

    def test_is_widget_or_parent_in_returns_false_for_unrelated_widget(self):
        self.assertFalse(is_widget_or_parent_in(FakeWidget(), [FakeWidget()]))

    def test_should_clear_selection_only_for_registered_background_clicks(self):
        source = FakeWidget(child=None)

        self.assertTrue(should_clear_selection_for_click(source, object(), [source], []))
        self.assertFalse(should_clear_selection_for_click(source, object(), [], []))

    def test_should_clear_selection_keeps_selection_when_child_is_task_widget(self):
        task_widget = FakeWidget()
        child = FakeWidget(parent=task_widget)
        source = FakeWidget(child=child)

        self.assertFalse(
            should_clear_selection_for_click(source, object(), [source], [task_widget])
        )


if __name__ == "__main__":
    unittest.main()