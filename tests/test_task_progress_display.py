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

from gui.tasks.task_progress_display import (
    build_task_progress_display,
    parse_percent_value,
    strip_ansi,
)
from locales.strings import STR


class TaskProgressDisplayTests(unittest.TestCase):
    def test_strip_ansi_removes_terminal_sequences(self):
        self.assertEqual(strip_ansi("\x1b[0;32m42.7%\x1b[0m"), "42.7%")

    def test_parse_percent_value_returns_integer_progress(self):
        self.assertEqual(parse_percent_value("42.7%"), 42)
        self.assertEqual(parse_percent_value("100%"), 100)

    def test_parse_percent_value_returns_none_for_non_numeric_text(self):
        self.assertIsNone(parse_percent_value("N/A"))

    def test_build_task_progress_display_uses_speed_status(self):
        display = build_task_progress_display(
            {
                "_percent_str": "\x1b[0;32m42.7%\x1b[0m",
                "downloaded_bytes": 1024,
                "total_bytes": 2048,
                "_speed_str": "\x1b[0;33m1.00MiB/s\x1b[0m",
                "status": "downloading",
            }
        )

        self.assertEqual(display.percent_text, "42.7%")
        self.assertEqual(display.progress_value, 42)
        self.assertEqual(display.size_text, "1.00 KiB / 2.00 KiB")
        self.assertEqual(
            display.status_text,
            STR.STATUS_DOWNLOADING_SPEED.format(speed="1.00MiB/s"),
        )

    def test_build_task_progress_display_prefers_postprocessing_status(self):
        display = build_task_progress_display(
            {
                "_percent_str": "100%",
                "downloaded_bytes": 4096,
                "total_bytes_estimate": 4096,
                "_speed_str": "1.00MiB/s",
                "status": "postprocessing",
            }
        )

        self.assertEqual(display.size_text, "4.00 KiB / 4.00 KiB")
        self.assertEqual(display.status_text, STR.STATUS_CONVERTING)


if __name__ == "__main__":
    unittest.main()