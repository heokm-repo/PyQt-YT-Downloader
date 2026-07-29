import ast
import os
import sys
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "src"
TEST_APPDATA = ROOT / "tests" / ".appdata"
TEST_APPDATA.mkdir(exist_ok=True)
os.environ["APPDATA"] = str(TEST_APPDATA)
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from core.ytdlp import wrapper as ytdlp_wrapper
from core.scheduler import DownloadScheduler
from core.workers import DownloadWorker
from constants import STATUS_DOWNLOADING


class ExceptionHandlingPolicyTests(unittest.TestCase):
    def test_no_exception_handler_is_silent_pass_only(self):
        offenders = []
        for path in SRC.rglob("*.py"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler):
                    meaningful = [stmt for stmt in node.body if not isinstance(stmt, ast.Pass)]
                    if not meaningful:
                        offenders.append(f"{path.relative_to(ROOT)}:{node.lineno}")

        self.assertEqual(offenders, [])

    def test_ytdlp_kill_process_logs_taskkill_fallback(self):
        class FakeProcess:
            pid = 12345

            def __init__(self):
                self.kill_called = False

            def poll(self):
                return None

            def kill(self):
                self.kill_called = True

            def wait(self, timeout=None):
                return 0

        fake_process = FakeProcess()
        wrapper = ytdlp_wrapper.YtDlpWrapper("yt-dlp.exe")

        with patch.object(ytdlp_wrapper.os, "name", "nt"),              patch.object(ytdlp_wrapper.subprocess, "run", side_effect=OSError("blocked")),              patch.object(ytdlp_wrapper.log, "debug") as debug_log:
            wrapper._kill_process(fake_process)

        self.assertTrue(fake_process.kill_called)
        self.assertTrue(any("taskkill failed" in str(call) for call in debug_log.call_args_list))

    def test_worker_progress_hook_logs_handler_errors(self):
        scheduler = DownloadScheduler()
        worker = DownloadWorker(
            scheduler.download_queue,
            scheduler.stop_event,
            scheduler.pause_event,
            scheduler,
        )
        worker.current_task_id = 77

        with patch.object(worker, "_handle_downloading_status", side_effect=RuntimeError("boom")),              patch("core.workers.log.warning") as warning_log:
            worker._progress_hook({"status": STATUS_DOWNLOADING})

        warning_log.assert_called_once()
        self.assertIn("Progress update handling failed", warning_log.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
