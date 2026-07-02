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

from constants import MSG_0_PERCENT, TaskStatus
from gui.tasks.task_terminal_display import (
    build_failed_display,
    build_finished_display,
    build_paused_display,
    build_started_display,
)
from locales.strings import STR
from resources.styles import (
    PROGRESS_BAR_ERROR_STYLE,
    PROGRESS_BAR_FINISHED_STYLE,
    STATUS_LABEL_ERROR_STYLE,
    STATUS_LABEL_SUCCESS_STYLE,
    STATUS_LABEL_WARNING_STYLE,
)


class TaskTerminalDisplayTests(unittest.TestCase):
    def test_build_finished_display_sets_completion_values(self):
        display = build_finished_display(2048)

        self.assertEqual(display.status, TaskStatus.FINISHED)
        self.assertEqual(display.status_text, STR.STATUS_COMPLETED)
        self.assertEqual(display.status_style, STATUS_LABEL_SUCCESS_STYLE)
        self.assertEqual(display.progress_style, PROGRESS_BAR_FINISHED_STYLE)
        self.assertEqual(display.progress_value, 100)
        self.assertEqual(display.percent_text, MSG_0_PERCENT.replace("0", "100"))
        self.assertEqual(display.size_text, "2.00 KiB")

    def test_build_finished_display_omits_size_without_file_size(self):
        self.assertIsNone(build_finished_display().size_text)

    def test_build_failed_display_sets_error_values(self):
        display = build_failed_display("boom")

        self.assertEqual(display.status, TaskStatus.FAILED)
        self.assertEqual(display.status_text, STR.STATUS_FAILED_FMT.format(message="boom"))
        self.assertEqual(display.status_style, STATUS_LABEL_ERROR_STYLE)
        self.assertEqual(display.progress_style, PROGRESS_BAR_ERROR_STYLE)

    def test_build_paused_display_sets_warning_values(self):
        display = build_paused_display()

        self.assertEqual(display.status, TaskStatus.PAUSED)
        self.assertEqual(display.status_text, STR.STATUS_PAUSED)
        self.assertEqual(display.status_style, STATUS_LABEL_WARNING_STYLE)

    def test_build_started_display_sets_preparing_values(self):
        display = build_started_display()

        self.assertEqual(display.status, TaskStatus.DOWNLOADING)
        self.assertEqual(display.status_text, STR.STATUS_PREPARING)
        self.assertIsNone(display.status_style)
        self.assertIsNone(display.progress_style)


if __name__ == "__main__":
    unittest.main()