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
from gui.tasks.task_button_config import get_task_button_specs


class TaskButtonConfigTests(unittest.TestCase):
    def test_downloading_buttons_allow_pause_and_cancel(self):
        specs = get_task_button_specs(TaskStatus.DOWNLOADING)

        self.assertEqual([spec.action for spec in specs], ["pause", "delete_file"])
        self.assertEqual([spec.icon_name for spec in specs], ["mdi.pause", "mdi.delete"])

    def test_finished_buttons_allow_file_actions_then_remove(self):
        specs = get_task_button_specs(TaskStatus.FINISHED)

        self.assertEqual(
            [spec.action for spec in specs],
            ["play", "open_folder", "delete_file", "remove"],
        )

    def test_paused_failed_and_waiting_buttons(self):
        self.assertEqual(
            [spec.action for spec in get_task_button_specs(TaskStatus.PAUSED)],
            ["resume", "remove"],
        )
        self.assertEqual(
            [spec.action for spec in get_task_button_specs(TaskStatus.FAILED)],
            ["retry", "remove"],
        )
        self.assertEqual(
            [spec.action for spec in get_task_button_specs(TaskStatus.WAITING)],
            ["remove"],
        )


if __name__ == "__main__":
    unittest.main()