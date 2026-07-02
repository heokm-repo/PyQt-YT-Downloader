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

from gui.tasks.task_context_callbacks import build_task_context_callbacks


class FakeTaskActions:
    def __init__(self, calls):
        self.calls = calls

    def copy_url(self, task_id):
        self.calls.append(("copy_url", task_id))


class FakeWindow:
    def __init__(self):
        self.calls = []
        self.task_actions = FakeTaskActions(self.calls)

    def play_file(self, task_id):
        self.calls.append(("play_file", task_id))

    def _open_folders_for_selected(self):
        self.calls.append(("open_folder", None))

    def _pause_selected_tasks(self):
        self.calls.append(("pause", None))

    def _resume_selected_tasks(self):
        self.calls.append(("resume", None))

    def _retry_selected_tasks(self):
        self.calls.append(("retry", None))

    def _delete_files_for_selected(self):
        self.calls.append(("delete_file", None))

    def _remove_selected_from_list(self):
        self.calls.append(("remove", None))

    def _remove_all_completed_from_list(self):
        self.calls.append(("remove_all_completed", None))


class TaskContextCallbacksTests(unittest.TestCase):
    def test_first_selected_id_is_used_for_single_task_actions(self):
        window = FakeWindow()
        callbacks = build_task_context_callbacks(window, [10, 20])

        callbacks["play"]()
        callbacks["copy_url"]()

        self.assertEqual(window.calls, [("play_file", 10), ("copy_url", 10)])

    def test_empty_selection_single_task_actions_are_noops(self):
        window = FakeWindow()
        callbacks = build_task_context_callbacks(window, [])

        callbacks["play"]()
        callbacks["copy_url"]()

        self.assertEqual(window.calls, [])

    def test_selection_actions_delegate_to_window_methods(self):
        window = FakeWindow()
        callbacks = build_task_context_callbacks(window, [10])

        for key in ["open_folder", "pause", "resume", "retry", "delete_file", "remove", "remove_all_completed"]:
            callbacks[key]()

        self.assertEqual(
            window.calls,
            [
                ("open_folder", None),
                ("pause", None),
                ("resume", None),
                ("retry", None),
                ("delete_file", None),
                ("remove", None),
                ("remove_all_completed", None),
            ],
        )


if __name__ == "__main__":
    unittest.main()
