import os
import sys
import unittest
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.tasks.task_selection_plan import (
    selected_tasks_for_ids,
    selected_task_ids_matching,
    should_confirm_multiple_items,
    task_ids_with_status,
    tasks_except_id,
)


@dataclass
class FakeTask:
    id: int
    status: TaskStatus


class TaskSelectionPlanTests(unittest.TestCase):
    def test_selected_tasks_for_ids_returns_tasks_in_task_order(self):
        first = FakeTask(1, TaskStatus.FINISHED)
        second = FakeTask(2, TaskStatus.WAITING)
        third = FakeTask(3, TaskStatus.FAILED)

        self.assertEqual(
            selected_tasks_for_ids([3, 1], [first, second, third]),
            [first, third],
        )

    def test_tasks_except_id_removes_matching_task(self):
        first = FakeTask(1, TaskStatus.FINISHED)
        second = FakeTask(2, TaskStatus.WAITING)

        self.assertEqual(tasks_except_id([first, second], 1), [second])

    def test_selected_task_ids_matching_uses_predicate_and_preserves_order(self):
        tasks = [
            FakeTask(1, TaskStatus.FINISHED),
            FakeTask(2, TaskStatus.WAITING),
            FakeTask(3, TaskStatus.DOWNLOADING),
        ]

        self.assertEqual(
            selected_task_ids_matching(
                [3, 99, 2, 1],
                tasks,
                lambda task: task.status in (TaskStatus.DOWNLOADING, TaskStatus.WAITING),
            ),
            [3, 2],
        )

    def test_selected_task_ids_with_status_preserves_selected_order(self):
        tasks = [
            FakeTask(1, TaskStatus.FINISHED),
            FakeTask(2, TaskStatus.WAITING),
            FakeTask(3, TaskStatus.FINISHED),
        ]

        self.assertEqual(
            selected_task_ids_matching([3, 2, 1], tasks, lambda task: task.status == TaskStatus.FINISHED),
            [3, 1],
        )

    def test_selected_task_ids_with_status_ignores_missing_ids(self):
        tasks = [FakeTask(1, TaskStatus.FINISHED)]

        self.assertEqual(
            selected_task_ids_matching([99, 1], tasks, lambda task: task.status == TaskStatus.FINISHED),
            [1],
        )

    def test_task_ids_with_status_preserves_task_order(self):
        tasks = [
            FakeTask(1, TaskStatus.FINISHED),
            FakeTask(2, TaskStatus.FAILED),
            FakeTask(3, TaskStatus.FINISHED),
        ]

        self.assertEqual(task_ids_with_status(tasks, TaskStatus.FINISHED), [1, 3])

    def test_should_confirm_multiple_items_only_for_two_or_more(self):
        self.assertFalse(should_confirm_multiple_items(0))
        self.assertFalse(should_confirm_multiple_items(1))
        self.assertTrue(should_confirm_multiple_items(2))


if __name__ == "__main__":
    unittest.main()
