import os
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import KEY_DOWNLOAD_FOLDER, TaskStatus, YTDL_TEMP_DIR
from gui.tasks.paused_task_cleanup import cleanup_cancelled_paused_tasks
from locales.strings import STR


@dataclass
class FakeTask:
    id: int
    settings: dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PAUSED


class FakeWidget:
    def __init__(self):
        self.failed_message = None

    def set_failed(self, message):
        self.failed_message = message


class PausedTaskCleanupTests(unittest.TestCase):
    def test_cleanup_deletes_temp_folder_and_marks_tasks_failed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / YTDL_TEMP_DIR
            temp_dir.mkdir()
            (temp_dir / "fragment.part").write_text("data", encoding="utf-8")
            task = FakeTask(1, {KEY_DOWNLOAD_FOLDER: tmpdir})
            widget = FakeWidget()

            cleanup_cancelled_paused_tasks([task], {1: widget})

            self.assertFalse(temp_dir.exists())
            self.assertEqual(task.status, TaskStatus.FAILED)
            self.assertEqual(widget.failed_message, STR.STATUS_PAUSED_CANCELLED)

    def test_cleanup_handles_duplicate_save_paths_once_but_marks_all_tasks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / YTDL_TEMP_DIR
            temp_dir.mkdir()
            tasks = [FakeTask(1, {KEY_DOWNLOAD_FOLDER: tmpdir}), FakeTask(2, {KEY_DOWNLOAD_FOLDER: tmpdir})]
            widgets = {1: FakeWidget(), 2: FakeWidget()}

            cleanup_cancelled_paused_tasks(tasks, widgets)

            self.assertFalse(temp_dir.exists())
            self.assertTrue(all(task.status == TaskStatus.FAILED for task in tasks))
            self.assertEqual(widgets[1].failed_message, STR.STATUS_PAUSED_CANCELLED)
            self.assertEqual(widgets[2].failed_message, STR.STATUS_PAUSED_CANCELLED)

    def test_cleanup_marks_task_failed_without_widget(self):
        task = FakeTask(1, {KEY_DOWNLOAD_FOLDER: ""})

        cleanup_cancelled_paused_tasks([task], {})

        self.assertEqual(task.status, TaskStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
