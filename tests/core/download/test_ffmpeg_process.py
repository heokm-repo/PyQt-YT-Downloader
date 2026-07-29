import io
import os
import subprocess
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import PROCESS_TERMINATE_WAIT_SEC
from core.download.ffmpeg_process import run_ffmpeg_command


class FfmpegProcessTests(unittest.TestCase):
    def test_cancellation_wait_is_bounded_and_reports_unconfirmed_termination(self):
        class StuckProcess:
            returncode = None
            stderr = io.StringIO("")

            def __init__(self):
                self.wait_timeouts = []

            def poll(self):
                return None

            def kill(self):
                return None

            def wait(self, timeout=None):
                self.wait_timeouts.append(timeout)
                raise subprocess.TimeoutExpired("ffmpeg", timeout)

        process = StuckProcess()
        stop_results = iter((False, True))

        with patch(
            "core.download.ffmpeg_process.subprocess.Popen",
            return_value=process,
        ), patch("core.download.ffmpeg_process.time.sleep"):
            result = run_ffmpeg_command(
                ["ffmpeg.exe"],
                stop_check=lambda: next(stop_results),
                timeout_sec=60,
                timeout_error="timed out",
            )

        self.assertFalse(result.success)
        self.assertFalse(result.paused)
        self.assertFalse(result.process_stopped)
        self.assertIn("could not be stopped", result.error)
        self.assertEqual(process.wait_timeouts, [PROCESS_TERMINATE_WAIT_SEC])


if __name__ == "__main__":
    unittest.main()
