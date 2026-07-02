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
from gui.tasks.task_action_state import (
    is_pausable_status,
    is_resumable_status,
    is_retryable_status,
)


class TaskActionStateTests(unittest.TestCase):
    def test_only_downloading_and_waiting_are_pausable(self):
        self.assertTrue(is_pausable_status(TaskStatus.DOWNLOADING))
        self.assertTrue(is_pausable_status(TaskStatus.WAITING))
        self.assertFalse(is_pausable_status(TaskStatus.PAUSED))
        self.assertFalse(is_pausable_status(TaskStatus.FINISHED))

    def test_only_paused_is_resumable(self):
        self.assertTrue(is_resumable_status(TaskStatus.PAUSED))
        self.assertFalse(is_resumable_status(TaskStatus.WAITING))
        self.assertFalse(is_resumable_status(TaskStatus.FAILED))

    def test_only_failed_is_retryable(self):
        self.assertTrue(is_retryable_status(TaskStatus.FAILED))
        self.assertFalse(is_retryable_status(TaskStatus.PAUSED))
        self.assertFalse(is_retryable_status(TaskStatus.FINISHED))


if __name__ == "__main__":
    unittest.main()