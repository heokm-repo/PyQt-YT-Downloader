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
from gui.tasks.task_load_plan import (
    build_loaded_tasks,
    find_paused_tasks,
    handle_paused_task_restore,
)


@dataclass
class FakeTask:
    id: int
    status: TaskStatus


class TaskLoadPlanTests(unittest.TestCase):
    def test_build_loaded_tasks_converts_dicts_and_tracks_max_id(self):
        tasks, max_id = build_loaded_tasks(
            [
                {"id": 3, "url": "https://example.test/3", "status": "finished"},
                {"id": 7, "url": "https://example.test/7", "status": "paused"},
            ]
        )

        self.assertEqual([task.id for task in tasks], [3, 7])
        self.assertEqual([task.status for task in tasks], [TaskStatus.FINISHED, TaskStatus.PAUSED])
        self.assertEqual(max_id, 7)

    def test_build_loaded_tasks_handles_empty_input(self):
        tasks, max_id = build_loaded_tasks([])

        self.assertEqual(tasks, [])
        self.assertEqual(max_id, 0)

    def test_find_paused_tasks_filters_only_paused_tasks(self):
        tasks, _ = build_loaded_tasks(
            [
                {"id": 1, "status": "waiting"},
                {"id": 2, "status": "paused"},
                {"id": 3, "status": "failed"},
            ]
        )

        paused = find_paused_tasks(tasks)

        self.assertEqual([task.id for task in paused], [2])

    def test_handle_paused_task_restore_skips_callbacks_without_paused_tasks(self):
        calls = []

        result = handle_paused_task_restore(
            [FakeTask(1, TaskStatus.FINISHED)],
            lambda: calls.append("confirm") or True,
            lambda task_id: calls.append(("resume", task_id)),
            lambda tasks: calls.append(("cleanup", tasks)),
        )

        self.assertEqual(result.paused_count, 0)
        self.assertFalse(result.resumed)
        self.assertFalse(result.cleaned_up)
        self.assertEqual(calls, [])

    def test_handle_paused_task_restore_resumes_confirmed_tasks(self):
        resumed_ids = []
        cleaned_ids = []

        result = handle_paused_task_restore(
            [
                FakeTask(2, TaskStatus.PAUSED),
                FakeTask(3, TaskStatus.FAILED),
                FakeTask(4, TaskStatus.PAUSED),
            ],
            lambda: True,
            resumed_ids.append,
            lambda tasks: cleaned_ids.extend(task.id for task in tasks),
        )

        self.assertEqual(resumed_ids, [2, 4])
        self.assertEqual(cleaned_ids, [])
        self.assertEqual(result.paused_count, 2)
        self.assertTrue(result.resumed)
        self.assertFalse(result.cleaned_up)

    def test_handle_paused_task_restore_cleans_up_declined_tasks(self):
        resumed_ids = []
        cleaned_ids = []

        result = handle_paused_task_restore(
            [FakeTask(2, TaskStatus.PAUSED)],
            lambda: False,
            resumed_ids.append,
            lambda tasks: cleaned_ids.extend(task.id for task in tasks),
        )

        self.assertEqual(resumed_ids, [])
        self.assertEqual(cleaned_ids, [2])
        self.assertEqual(result.paused_count, 1)
        self.assertFalse(result.resumed)
        self.assertTrue(result.cleaned_up)


if __name__ == "__main__":
    unittest.main()