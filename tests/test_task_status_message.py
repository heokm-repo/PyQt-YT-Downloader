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

from constants import TaskStatus
from data.models import DownloadTask
from gui.tasks.task_status_message import build_task_status_message


def make_task(task_id, status):
    return DownloadTask(
        id=task_id,
        url=f"https://example.invalid/{task_id}",
        status=status,
    )


class TaskStatusMessageTests(unittest.TestCase):
    def test_build_task_status_message_returns_ready_for_empty_tasks(self):
        self.assertEqual(
            build_task_status_message([], "Ready", "Errors: {count}", "Done: {finished}/{total}"),
            "Ready",
        )

    def test_build_task_status_message_prefers_failure_message(self):
        message = build_task_status_message(
            [make_task(1, TaskStatus.FINISHED), make_task(2, TaskStatus.FAILED)],
            "Ready",
            "Errors: {count}",
            "Done: {finished}/{total}",
        )

        self.assertEqual(message, "Errors: 1")

    def test_build_task_status_message_reports_completed_count(self):
        message = build_task_status_message(
            [make_task(1, TaskStatus.FINISHED), make_task(2, TaskStatus.WAITING)],
            "Ready",
            "Errors: {count}",
            "Done: {finished}/{total}",
        )

        self.assertEqual(message, "Done: 1/2")


if __name__ == "__main__":
    unittest.main()