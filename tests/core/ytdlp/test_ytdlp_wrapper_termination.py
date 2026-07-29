import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import MagicMock, call, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import (
    MSG_PAUSED_BY_USER,
    PROCESS_MONITOR_INTERVAL_SEC,
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
    def test_timeout_result_waits_for_slow_termination_to_complete(self):
        class RunningProcess:
            def poll(self):
                return None

            def wait(self, timeout=None):
                raise AssertionError("process.wait must not run after timeout")

        process = RunningProcess()
        terminate_started = threading.Event()
        allow_termination = threading.Event()

        def slow_terminate(proc):
            terminate_started.set()
            allow_termination.wait(timeout=1)

        watchdog = ProcessWatchdog(
            process,
            None,
            slow_terminate,
            inactivity_timeout=0.02,
            poll_interval=0.01,
        )
        watchdog.start()
        self.assertTrue(terminate_started.wait(timeout=1))

        wrapper = YtDlpWrapper("yt-dlp.exe")
        result = []
        result_ready = threading.Event()

        def wait_for_result():
            result.append(
                wrapper._wait_for_download_result(
                    process,
                    [],
                    MagicMock(),
                    watchdog,
                )
            )
            result_ready.set()

        result_thread = threading.Thread(target=wait_for_result)
        result_thread.start()
        try:
            self.assertFalse(result_ready.wait(timeout=0.05))
            allow_termination.set()
            self.assertTrue(result_ready.wait(timeout=1))
        finally:
            allow_termination.set()
            result_thread.join(timeout=1)
            watchdog.close(0.2)

        self.assertTrue(watchdog.termination_complete.is_set())
        self.assertEqual(result, [(False, "Download timeout")])

    def test_stdout_eof_relies_on_inactivity_watchdog_until_process_exits(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = MagicMock()
        process.returncode = 0
        process.wait.side_effect = [
            subprocess.TimeoutExpired(
                "yt-dlp",
                PROCESS_MONITOR_INTERVAL_SEC,
            ),
            0,
        ]
        watchdog = MagicMock()
        watchdog.stop_requested.is_set.return_value = False
        watchdog.inactivity_timed_out.is_set.return_value = False
        watchdog.check_stop_requested.return_value = False

        result = wrapper._wait_for_download_result(
            process,
            [],
            MagicMock(),
            watchdog,
        )

        self.assertEqual(result, (True, "Download complete"))
        self.assertEqual(
            process.wait.call_args_list,
            [
                call(timeout=PROCESS_MONITOR_INTERVAL_SEC),
                call(timeout=PROCESS_MONITOR_INTERVAL_SEC),
            ],
        )
        watchdog.request_timeout.assert_not_called()

    def test_windows_taskkill_has_a_bounded_timeout_and_falls_back(self):
        class RunningProcess:
            pid = 12345

            def __init__(self):
                self.kill_called = False

            def poll(self):
                return None

            def kill(self):
                self.kill_called = True

            def wait(self, timeout=None):
                return 0

        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = RunningProcess()

        with patch("core.ytdlp.wrapper.os.name", "nt"), \
             patch(
                 "core.ytdlp.wrapper.subprocess.run",
                 side_effect=subprocess.TimeoutExpired("taskkill", 5),
             ) as taskkill:
            wrapper._kill_process(process)

        self.assertTrue(process.kill_called)
        self.assertEqual(
            taskkill.call_args.kwargs["timeout"],
            PROCESS_TERMINATE_WAIT_SEC,
        )
        self.assertTrue(taskkill.call_args.kwargs["check"])


if __name__ == "__main__":
    unittest.main()
