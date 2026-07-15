import os
import sys
import unittest
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.tasks.context_menu_plan import (
    build_context_menu_visibility,
    context_menu_status_flags,
    has_completed_task,
)


@dataclass
class FakeTask:
    status: TaskStatus


class ContextMenuPlanTests(unittest.TestCase):
    def test_context_menu_status_flags_reports_selected_statuses(self):
        flags = context_menu_status_flags(
            [
                FakeTask(TaskStatus.FINISHED),
                FakeTask(TaskStatus.PAUSED),
                FakeTask(TaskStatus.FAILED),
            ]
        )

        self.assertTrue(flags.finished)
        self.assertTrue(flags.paused)
        self.assertTrue(flags.failed)
        self.assertFalse(flags.downloading)
        self.assertFalse(flags.waiting)

    def test_has_completed_task_checks_all_tasks(self):
        self.assertFalse(has_completed_task([FakeTask(TaskStatus.WAITING)]))
        self.assertTrue(has_completed_task([FakeTask(TaskStatus.FINISHED)]))

    def test_single_finished_task_shows_file_actions(self):
        visibility = build_context_menu_visibility(
            [FakeTask(TaskStatus.FINISHED)],
            [FakeTask(TaskStatus.FINISHED)],
        )

        self.assertTrue(visibility.play)
        self.assertTrue(visibility.open_folder)
        self.assertTrue(visibility.copy_url)
        self.assertTrue(visibility.retry)
        self.assertTrue(visibility.delete_file)
        self.assertTrue(visibility.remove)
        self.assertTrue(visibility.remove_completed)

    def test_multiple_finished_tasks_hide_single_item_actions(self):
        visibility = build_context_menu_visibility(
            [FakeTask(TaskStatus.FINISHED), FakeTask(TaskStatus.FINISHED)],
            [],
        )

        self.assertFalse(visibility.play)
        self.assertFalse(visibility.open_folder)
        self.assertFalse(visibility.copy_url)
        self.assertTrue(visibility.retry)
        self.assertTrue(visibility.delete_file)
        self.assertTrue(visibility.remove)
        self.assertFalse(visibility.remove_completed)

    def test_active_paused_and_failed_statuses_show_matching_actions(self):
        visibility = build_context_menu_visibility(
            [
                FakeTask(TaskStatus.WAITING),
                FakeTask(TaskStatus.PAUSED),
                FakeTask(TaskStatus.FAILED),
            ],
            [],
        )

        self.assertTrue(visibility.pause)
        self.assertTrue(visibility.resume)
        self.assertTrue(visibility.retry)


if __name__ == "__main__":
    unittest.main()
