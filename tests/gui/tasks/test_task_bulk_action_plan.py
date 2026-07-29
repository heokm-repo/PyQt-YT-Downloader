import os
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.tasks.task_bulk_action_plan import (
    build_delete_files_plan,
    build_remove_completed_plan,
    build_remove_selected_plan,
    folders_to_open_for_selected,
)


@dataclass
class FakeTask:
    id: int
    status: TaskStatus
    output_path: str = ""


class TaskBulkActionPlanTests(unittest.TestCase):
    def test_build_delete_files_plan_keeps_finished_selected_tasks(self):
        tasks = [
            FakeTask(1, TaskStatus.FINISHED),
            FakeTask(2, TaskStatus.WAITING),
            FakeTask(3, TaskStatus.FINISHED),
        ]

        plan = build_delete_files_plan([3, 2, 1], tasks)

        self.assertEqual(plan.task_ids, [3, 1])
        self.assertEqual(plan.count, 2)
        self.assertTrue(plan.has_tasks)
        self.assertTrue(plan.needs_confirmation)

    def test_build_delete_files_plan_without_finished_tasks_has_no_confirmation(self):
        tasks = [FakeTask(1, TaskStatus.WAITING)]

        plan = build_delete_files_plan([1], tasks)

        self.assertEqual(plan.task_ids, [])
        self.assertFalse(plan.has_tasks)
        self.assertFalse(plan.needs_confirmation)

    def test_build_delete_files_plan_includes_failed_task_with_retained_output(self):
        tasks = [
            FakeTask(
                1,
                TaskStatus.FAILED,
                "C:/Downloads/unfinalized-source.mp4",
            )
        ]

        plan = build_delete_files_plan([1], tasks)

        self.assertEqual(plan.task_ids, [1])
        self.assertTrue(plan.needs_confirmation)

    def test_build_delete_files_plan_excludes_active_task_with_stale_output(self):
        tasks = [
            FakeTask(
                1,
                TaskStatus.DOWNLOADING,
                "C:/Downloads/old.mp4",
            )
        ]

        plan = build_delete_files_plan([1], tasks)

        self.assertEqual(plan.task_ids, [])

    def test_build_remove_selected_plan_preserves_order_and_confirms_many(self):
        plan = build_remove_selected_plan([3, 1])

        self.assertEqual(plan.task_ids, [3, 1])
        self.assertEqual(plan.count, 2)
        self.assertTrue(plan.needs_confirmation)

    def test_build_remove_selected_plan_does_not_confirm_single_item(self):
        plan = build_remove_selected_plan([7])

        self.assertEqual(plan.task_ids, [7])
        self.assertFalse(plan.needs_confirmation)

    def test_build_remove_completed_plan_uses_task_order(self):
        tasks = [
            FakeTask(1, TaskStatus.FINISHED),
            FakeTask(2, TaskStatus.FAILED),
            FakeTask(3, TaskStatus.FINISHED),
        ]

        plan = build_remove_completed_plan(tasks)

        self.assertEqual(plan.task_ids, [1, 3])
        self.assertTrue(plan.needs_confirmation)

    def test_folders_to_open_for_selected_preserves_selection_order_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            first_folder = Path(tmpdir) / "first"
            second_folder = Path(tmpdir) / "second"
            first_folder.mkdir()
            second_folder.mkdir()
            tasks = [
                FakeTask(1, TaskStatus.FINISHED, str(first_folder / "one.mp4")),
                FakeTask(2, TaskStatus.FINISHED, str(second_folder / "two.mp4")),
                FakeTask(3, TaskStatus.FINISHED, str(first_folder / "three.mp4")),
            ]

            folders = folders_to_open_for_selected([2, 99, 1, 3], tasks)

        self.assertEqual(folders, [str(second_folder), str(first_folder)])


if __name__ == "__main__":
    unittest.main()
