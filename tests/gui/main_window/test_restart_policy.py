import os
import sys
import unittest
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.main_window.restart_policy import has_restart_sensitive_tasks


class RestartPolicyTests(unittest.TestCase):
    def test_downloading_and_waiting_tasks_require_restart_notice(self):
        for status in (TaskStatus.DOWNLOADING, TaskStatus.WAITING):
            with self.subTest(status=status):
                self.assertTrue(
                    has_restart_sensitive_tasks([SimpleNamespace(status=status)])
                )

    def test_paused_and_terminal_tasks_do_not_require_active_notice(self):
        tasks = [
            SimpleNamespace(status=TaskStatus.PAUSED),
            SimpleNamespace(status=TaskStatus.FINISHED),
            SimpleNamespace(status=TaskStatus.FAILED),
        ]

        self.assertFalse(has_restart_sensitive_tasks(tasks))


if __name__ == "__main__":
    unittest.main()
