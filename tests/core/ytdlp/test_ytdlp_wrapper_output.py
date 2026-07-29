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
    def test_ytdlp_environment_disables_plugin_loading(self):
        self.assertEqual(_ytdlp_environment()["YTDLP_NO_PLUGINS"], "1")
        self.assertEqual(_ytdlp_environment()["PYTHONIOENCODING"], "utf-8")

    def test_stdout_progress_loop_tracks_current_file_and_completion(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        events = []
        process = FakeProcess(
            [
                "[download] Destination: sample.mp4\n",
                "[download] 50.0% of 10.0MiB at 1.0MiB/s ETA 00:05\n",
                "[download] 100% of 10.0MiB in 00:10\n",
                "__YTDLP_FINAL_PATH__:C:/Downloads/한글 제목.mp4\n",
            ]
        )

        stopped = wrapper._run_stdout_progress_loop(process, events.append, None)

        self.assertFalse(stopped)
        self.assertEqual(events[0]["status"], "downloading")
        self.assertEqual(events[0]["filename"], "sample.mp4")
        self.assertEqual(events[-1], {"status": "finished", "filename": "sample.mp4"})
        self.assertEqual(wrapper.final_output_path, "C:/Downloads/한글 제목.mp4")

    def test_stdout_progress_loop_returns_stopped_when_stop_check_requests_stop(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = FakeProcess(["[download] Destination: sample.mp4\n"])
        killed = []

        def fake_kill(proc):
            killed.append(proc)

        wrapper._kill_process = fake_kill

        stopped = wrapper._run_stdout_progress_loop(process, lambda data: None, lambda: True)

        self.assertTrue(stopped)
        self.assertEqual(killed, [process])

    def test_stdout_progress_loop_emits_metadata_before_download_progress(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        calls = []
        metadata = {
            "id": "abc123",
            "title": "Example",
            "requested_formats": [{"format_id": "137"}, {"format_id": "140"}],
        }
        process = FakeProcess(
            [
                f"{YTDLP_METADATA_MARKER}{json.dumps(metadata)}\n",
                "[download] Destination: sample.mp4\n",
                "[download] 50.0% of 10.0MiB at 1.0MiB/s ETA 00:05\n",
            ]
        )

        stopped = wrapper._run_stdout_progress_loop(
            process,
            lambda event: calls.append(("progress", event)),
            None,
            lambda info: calls.append(("metadata", info)),
        )

        self.assertFalse(stopped)
        self.assertEqual(calls[0], ("metadata", metadata))
        self.assertEqual(calls[1][0], "progress")
        self.assertEqual(calls[1][1]["status"], "downloading")

    def test_malformed_metadata_warns_without_leaking_payload_and_continues(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        events = []
        secret_payload = '{"url":"https://signed.example.invalid/private"'
        process = FakeProcess(
            [
                f"{YTDLP_METADATA_MARKER}{secret_payload}\n",
                "[download] Destination: sample.mp4\n",
                "[download] 100% of 10.0MiB in 00:10\n",
            ]
        )

        with patch("core.ytdlp.wrapper.log.warning") as warning:
            stopped = wrapper._run_stdout_progress_loop(
                process,
                events.append,
                None,
                lambda info: None,
            )

        self.assertFalse(stopped)
        self.assertTrue(events)
        warning.assert_called_once_with("Failed to parse yt-dlp metadata output")
        self.assertNotIn(secret_payload, str(warning.call_args))

    def test_metadata_hook_failure_warns_without_leaking_payload_and_continues(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        events = []
        secret_url = "https://signed.example.invalid/private"
        process = FakeProcess(
            [
                f"{YTDLP_METADATA_MARKER}{json.dumps({'url': secret_url})}\n",
                "[download] Destination: sample.mp4\n",
                "[download] 100% of 10.0MiB in 00:10\n",
            ]
        )

        def failing_hook(info):
            raise RuntimeError(f"Cannot process {info['url']}")

        with patch("core.ytdlp.wrapper.log.warning") as warning:
            stopped = wrapper._run_stdout_progress_loop(
                process,
                events.append,
                None,
                failing_hook,
            )

        self.assertFalse(stopped)
        self.assertTrue(events)
        warning.assert_called_once_with("yt-dlp metadata hook failed (RuntimeError)")
        self.assertNotIn(secret_url, str(warning.call_args))

    def test_download_passes_optional_metadata_hook_to_stdout_loop(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")
        process = object()
        workspace = "C:/Downloads/.ytdl_temp/task"
        progress_hook = lambda event: None
        stop_check = lambda: False
        metadata_hook = lambda info: None
        process_watchdog = MagicMock()

        with patch.object(wrapper, "_start_download_process", return_value=process), \
             patch.object(wrapper, "_start_stderr_drain", return_value=object()), \
             patch.object(wrapper, "_run_stdout_progress_loop", return_value=False) as stdout_loop, \
             patch.object(wrapper, "_wait_for_download_result", return_value=(True, "ok")), \
             patch(
                 "core.ytdlp.wrapper.ProcessWatchdog",
                 return_value=process_watchdog,
             ):
            result = wrapper.download(
                "https://example.invalid/video",
                {
                    "temp_path": workspace,
                    "home_path": workspace,
                },
                progress_hook,
                stop_check=stop_check,
                metadata_hook=metadata_hook,
            )

        self.assertEqual(result, (True, "ok"))
        stdout_loop.assert_called_once_with(
            process,
            progress_hook,
            stop_check,
            metadata_hook,
            process_watchdog,
        )
        self.assertEqual(
            process_watchdog.method_calls[:2],
            [
                call.watch_output_directory(workspace),
                call.start(),
            ],
        )
        process_watchdog.close.assert_called_once()
