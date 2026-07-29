import os
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from gui.tasks.download_completion import (
    FailedDownloadAction,
    apply_failed_download_result,
    persist_download_output,
    record_successful_download,
    resolve_failed_download_action,
)
from locales.strings import STR


@dataclass
class FakeTask:
    status: TaskStatus = TaskStatus.WAITING
    output_path: str = ""
    meta: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)
    extractor: str = "youtube"
    video_id: str = "video-1"


class FakeHistoryManager:
    def __init__(self):
        self.entries = []

    def add_to_history(self, extractor, video_id, meta, task_format):
        self.entries.append((extractor, video_id, meta, task_format))


class FakeWidget:
    def __init__(self):
        self.calls = []

    def set_paused(self):
        self.calls.append(("set_paused", None))

    def set_failed(self, message):
        self.calls.append(("set_failed", message))


class DownloadCompletionTests(unittest.TestCase):
    def test_persist_download_output_stores_absolute_path_and_file_size(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "video.mp4"
            path.write_bytes(b"12345")
            task = FakeTask()

            resolved = persist_download_output(task, str(path), success=True)

        self.assertEqual(resolved, str(path.resolve()))
        self.assertEqual(task.output_path, str(path.resolve()))
        self.assertEqual(task.meta["file_size"], 5)

    def test_persist_download_output_does_not_store_size_on_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "video.mp4"
            path.write_bytes(b"12345")
            task = FakeTask()

            persist_download_output(task, str(path), success=False)

        self.assertEqual(task.meta, {})
        self.assertEqual(task.output_path, str(path.resolve()))

    def test_record_successful_download_marks_finished_and_adds_history(self):
        task = FakeTask(
            status=TaskStatus.DOWNLOADING,
            meta={"file_size": 42},
            settings={"format": "webm"},
            extractor="youtube",
            video_id="abc",
        )
        history = FakeHistoryManager()

        file_size = record_successful_download(task, history)

        self.assertEqual(file_size, 42)
        self.assertEqual(task.status, TaskStatus.FINISHED)
        self.assertEqual(history.entries, [("youtube", "abc", {"file_size": 42}, "webm")])

    def test_record_successful_download_handles_missing_task(self):
        history = FakeHistoryManager()

        file_size = record_successful_download(None, history)

        self.assertIsNone(file_size)
        self.assertEqual(history.entries, [])

    def test_resolve_failed_download_action_handles_pause_edge_states(self):
        self.assertEqual(
            resolve_failed_download_action(FakeTask(TaskStatus.PAUSED), STR.STATUS_PAUSED, STR.STATUS_PAUSED),
            FailedDownloadAction.IGNORE_ALREADY_PAUSED,
        )
        self.assertEqual(
            resolve_failed_download_action(FakeTask(TaskStatus.WAITING), STR.STATUS_PAUSED, STR.STATUS_PAUSED),
            FailedDownloadAction.IGNORE_RESUMING,
        )
        self.assertEqual(
            resolve_failed_download_action(FakeTask(TaskStatus.DOWNLOADING), STR.STATUS_PAUSED, STR.STATUS_PAUSED),
            FailedDownloadAction.PAUSE,
        )
        self.assertEqual(
            resolve_failed_download_action(FakeTask(TaskStatus.DOWNLOADING), "boom", STR.STATUS_PAUSED),
            FailedDownloadAction.FAIL,
        )

    def test_apply_failed_download_result_pauses_task_and_widget(self):
        task = FakeTask(TaskStatus.DOWNLOADING)
        widget = FakeWidget()

        action = apply_failed_download_result(task, widget, STR.STATUS_PAUSED, STR.STATUS_PAUSED)

        self.assertEqual(action, FailedDownloadAction.PAUSE)
        self.assertEqual(task.status, TaskStatus.PAUSED)
        self.assertEqual(widget.calls, [("set_paused", None)])

    def test_apply_failed_download_result_marks_failure(self):
        task = FakeTask(TaskStatus.DOWNLOADING)
        widget = FakeWidget()

        action = apply_failed_download_result(task, widget, "boom", STR.STATUS_PAUSED)

        self.assertEqual(action, FailedDownloadAction.FAIL)
        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(widget.calls, [("set_failed", "boom")])

    def test_apply_failed_download_result_leaves_ignored_pause_unchanged(self):
        task = FakeTask(TaskStatus.WAITING)
        widget = FakeWidget()

        action = apply_failed_download_result(task, widget, STR.STATUS_PAUSED, STR.STATUS_PAUSED)

        self.assertEqual(action, FailedDownloadAction.IGNORE_RESUMING)
        self.assertEqual(task.status, TaskStatus.WAITING)
        self.assertEqual(widget.calls, [])


if __name__ == "__main__":
    unittest.main()
