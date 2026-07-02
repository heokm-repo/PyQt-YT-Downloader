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
from gui.tasks.task_status_style import status_border_color
from resources.styles import (
    COLOR_DOWNLOADING,
    COLOR_ERROR,
    COLOR_FINISHED,
    COLOR_PAUSED,
    COLOR_WAITING,
)


class TaskStatusStyleTests(unittest.TestCase):
    def test_status_border_color_maps_known_statuses(self):
        self.assertEqual(status_border_color(TaskStatus.DOWNLOADING), COLOR_DOWNLOADING)
        self.assertEqual(status_border_color(TaskStatus.FINISHED), COLOR_FINISHED)
        self.assertEqual(status_border_color(TaskStatus.FAILED), COLOR_ERROR)
        self.assertEqual(status_border_color(TaskStatus.PAUSED), COLOR_PAUSED)
        self.assertEqual(status_border_color(TaskStatus.WAITING), COLOR_WAITING)

    def test_status_border_color_defaults_to_waiting(self):
        self.assertEqual(status_border_color("unknown"), COLOR_WAITING)


if __name__ == "__main__":
    unittest.main()