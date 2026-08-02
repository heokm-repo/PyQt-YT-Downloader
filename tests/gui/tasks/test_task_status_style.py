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

from constants import TaskStatus
from gui.tasks.task_status_style import status_border_color
from resources.colors import (
    COLOR_TASK_DOWNLOADING_BORDER,
    COLOR_TASK_FAILED_BORDER,
    COLOR_TASK_FINISHED_BORDER,
    COLOR_TASK_PAUSED_BORDER,
    COLOR_TASK_WAITING_BORDER,
)


class TaskStatusStyleTests(unittest.TestCase):
    def test_status_border_color_maps_known_statuses(self):
        self.assertEqual(status_border_color(TaskStatus.DOWNLOADING), COLOR_TASK_DOWNLOADING_BORDER)
        self.assertEqual(status_border_color(TaskStatus.FINISHED), COLOR_TASK_FINISHED_BORDER)
        self.assertEqual(status_border_color(TaskStatus.FAILED), COLOR_TASK_FAILED_BORDER)
        self.assertEqual(status_border_color(TaskStatus.PAUSED), COLOR_TASK_PAUSED_BORDER)
        self.assertEqual(status_border_color(TaskStatus.WAITING), COLOR_TASK_WAITING_BORDER)

    def test_status_border_color_defaults_to_waiting(self):
        self.assertEqual(status_border_color("unknown"), COLOR_TASK_WAITING_BORDER)


if __name__ == "__main__":
    unittest.main()
