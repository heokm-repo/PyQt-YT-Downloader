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
from core.task_summary import summarize_task_progress
from data.models import DownloadTask


def make_task(task_id, status):
    return DownloadTask(
        id=task_id,
        url=f"https://example.invalid/{task_id}",
        status=status,
    )


class TaskSummaryTests(unittest.TestCase):
    def test_empty_task_list_returns_zero_counts(self):
        summary = summarize_task_progress([])

        self.assertEqual(summary.total, 0)
        self.assertEqual(summary.finished, 0)
        self.assertEqual(summary.failed, 0)
        self.assertEqual(summary.in_progress, 0)
        self.assertFalse(summary.has_failures)

    def test_summary_counts_terminal_and_active_tasks(self):
        summary = summarize_task_progress([
            make_task(1, TaskStatus.WAITING),
            make_task(2, TaskStatus.DOWNLOADING),
            make_task(3, TaskStatus.PAUSED),
            make_task(4, TaskStatus.FINISHED),
            make_task(5, TaskStatus.FAILED),
        ])

        self.assertEqual(summary.total, 5)
        self.assertEqual(summary.finished, 1)
        self.assertEqual(summary.failed, 1)
        self.assertEqual(summary.in_progress, 3)
        self.assertTrue(summary.has_failures)


if __name__ == "__main__":
    unittest.main()
