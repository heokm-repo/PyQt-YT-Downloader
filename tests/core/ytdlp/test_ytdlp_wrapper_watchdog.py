import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import (
    MSG_PAUSED_BY_USER,
    PROCESS_TERMINATE_WAIT_SEC,
    YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC,
    YTDLP_METADATA_MARKER,
)
from core.ytdlp.process_watchdog import ProcessWatchdog, TerminationReason
from core.ytdlp.wrapper import YtDlpWrapper, _ytdlp_environment


class FakeStdout:
    def __init__(self, lines):
        self.lines = list(lines)

    def readline(self):
        if not self.lines:
            return ""
        return self.lines.pop(0)


class FakeProcess:
    def __init__(self, lines):
        self.stdout = FakeStdout(lines)
        self.killed = False

    def poll(self):
        return None


class YtDlpWrapperLifecycleTests(unittest.TestCase):
    def test_blocked_stdout_returns_when_inactivity_watchdog_expires(self):
        class BlockingStdout:
            def __init__(self):
                self.release = threading.Event()

            def readline(self):
                self.release.wait(timeout=2)
                return ""

        class HangingProcess:
            def __init__(self):
                self.stdout = BlockingStdout()

            def poll(self):
                return None

        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = HangingProcess()
        terminated = threading.Event()
        watchdog = ProcessWatchdog(
            process,
            None,
            lambda proc: terminated.set(),
            inactivity_timeout=0.05,
            poll_interval=0.01,
        )
        watchdog.start()

        started_at = time.monotonic()
        try:
            stopped = wrapper._run_stdout_progress_loop(
                process,
                lambda event: None,
                None,
                process_watchdog=watchdog,
            )
        finally:
            process.stdout.release.set()
            watchdog.close(0.2)

        self.assertFalse(stopped)
        self.assertTrue(terminated.is_set())
        self.assertTrue(watchdog.inactivity_timed_out.is_set())
        self.assertLess(time.monotonic() - started_at, 1)

    def test_stop_request_is_reported_before_simultaneous_timeout(self):
        class RunningProcess:
            def poll(self):
                return None

        stop_requested = threading.Event()
        stop_requested.set()
        terminated = []
        watchdog = ProcessWatchdog(
            RunningProcess(),
            stop_requested.is_set,
            lambda proc: terminated.append(proc),
            inactivity_timeout=0.01,
            poll_interval=0.01,
        )

        watchdog.start()
        try:
            deadline = time.monotonic() + 1
            while watchdog.termination_reason is None and time.monotonic() < deadline:
                time.sleep(0.005)
        finally:
            watchdog.close(0.2)

        self.assertEqual(
            watchdog.termination_reason,
            TerminationReason.STOP_REQUESTED,
        )
        self.assertTrue(watchdog.stop_requested.is_set())
        self.assertFalse(watchdog.inactivity_timed_out.is_set())
        self.assertEqual(len(terminated), 1)

    def test_output_activity_resets_inactivity_deadline(self):
        class RunningProcess:
            def poll(self):
                return None

        terminated = threading.Event()
        watchdog = ProcessWatchdog(
            RunningProcess(),
            None,
            lambda proc: terminated.set(),
            inactivity_timeout=0.12,
            poll_interval=0.01,
        )

        watchdog.start()
        try:
            time.sleep(0.07)
            watchdog.notify_activity()
            self.assertFalse(terminated.wait(timeout=0.07))
            self.assertTrue(terminated.wait(timeout=0.2))
        finally:
            watchdog.close(0.2)

        self.assertTrue(watchdog.inactivity_timed_out.is_set())

    def test_growing_ffmpeg_temp_file_resets_inactivity_deadline(self):
        class RunningProcess:
            def poll(self):
                return None

        terminated = threading.Event()
        watchdog = ProcessWatchdog(
            RunningProcess(),
            None,
            lambda proc: terminated.set(),
            inactivity_timeout=0.12,
            poll_interval=0.01,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            final_path = os.path.join(temp_dir, "video.mp4")
            ffmpeg_temp_path = os.path.join(temp_dir, "video.temp.mp4")
            watchdog.watch_output_path(final_path)
            watchdog.start()
            try:
                for _ in range(4):
                    time.sleep(0.06)
                    with open(ffmpeg_temp_path, "ab") as output_file:
                        output_file.write(b"x")
                self.assertFalse(terminated.is_set())
                self.assertTrue(terminated.wait(timeout=0.3))
            finally:
                watchdog.close(0.2)

        self.assertTrue(watchdog.inactivity_timed_out.is_set())

    def test_growing_file_in_task_workspace_resets_inactivity_deadline(self):
        class RunningProcess:
            def poll(self):
                return None

        terminated = threading.Event()
        watchdog = ProcessWatchdog(
            RunningProcess(),
            None,
            lambda proc: terminated.set(),
            inactivity_timeout=0.12,
            poll_interval=0.01,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            nested_directory = os.path.join(temp_dir, "nested")
            output_path = os.path.join(nested_directory, "unknown-name.temp.mp4")
            watchdog.watch_output_directory(temp_dir)
            watchdog.start()
            try:
                os.makedirs(nested_directory)
                for _ in range(4):
                    time.sleep(0.06)
                    with open(output_path, "ab") as output_file:
                        output_file.write(b"x")
                self.assertFalse(terminated.is_set())
                self.assertTrue(terminated.wait(timeout=0.3))
            finally:
                watchdog.close(0.2)

        self.assertTrue(watchdog.inactivity_timed_out.is_set())

    def test_wrapper_registers_destination_merger_and_final_candidates(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = FakeProcess(
            [
                "[download] Destination: video.f137.mp4\n",
                '[Merger] Merging formats into "merged.mp4"\n',
                (
                    "[VideoConvertor] Converting video from webm to mp4; "
                    "Destination: converted.mp4\n"
                ),
                "__YTDLP_FINAL_PATH__:final.mp4\n",
            ]
        )
        watchdog = MagicMock()
        watchdog.check_stop_requested.return_value = False
        watchdog.inactivity_timed_out.is_set.return_value = False

        stopped = wrapper._run_stdout_progress_loop(
            process,
            lambda event: None,
            None,
            process_watchdog=watchdog,
        )

        self.assertFalse(stopped)
        self.assertEqual(
            [call.args[0] for call in watchdog.watch_output_path.call_args_list],
            ["video.f137.mp4", "merged.mp4", "converted.mp4", "final.mp4"],
        )

    def test_normal_process_exit_is_not_reclassified_as_inactivity_timeout(self):
        class ExitedProcess:
            def poll(self):
                return 0

        terminated = threading.Event()
        watchdog = ProcessWatchdog(
            ExitedProcess(),
            None,
            lambda proc: terminated.set(),
            inactivity_timeout=0.02,
            poll_interval=0.01,
        )

        watchdog.start()
        try:
            time.sleep(0.05)
        finally:
            watchdog.close(0.2)

        self.assertFalse(terminated.is_set())
        self.assertFalse(watchdog.inactivity_timed_out.is_set())
        self.assertIsNone(watchdog.termination_reason)

    def test_stderr_output_also_resets_the_activity_deadline(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = MagicMock()
        process.stderr = FakeStdout(["warning one\n", "warning two\n"])
        output = []
        activity_hook = MagicMock()

        wrapper._drain_stderr(process, output, activity_hook)

        self.assertEqual(output, ["warning one\n", "warning two\n"])
        self.assertEqual(activity_hook.call_count, 2)

    def test_pause_result_takes_priority_over_timeout_result(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = MagicMock()
        stderr_thread = MagicMock()
        watchdog = MagicMock()
        watchdog.stop_requested.is_set.return_value = True
        watchdog.inactivity_timed_out.is_set.return_value = True

        result = wrapper._wait_for_download_result(
            process,
            [],
            stderr_thread,
            watchdog,
        )

        self.assertEqual(result, (False, MSG_PAUSED_BY_USER))
        process.wait.assert_not_called()
        watchdog.wait_for_termination.assert_called_once()
