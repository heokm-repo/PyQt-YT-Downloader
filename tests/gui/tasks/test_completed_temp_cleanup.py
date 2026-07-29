import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import KEY_DOWNLOAD_FOLDER, TaskStatus, YTDL_TEMP_DIR
from data.models import DownloadTask
from gui.tasks.completed_temp_cleanup import cleanup_temp_dirs_if_all_finished


def make_task(task_id, status, download_folder):
    return DownloadTask(
        id=task_id,
        url=f"https://example.invalid/{task_id}",
        status=status,
        settings={KEY_DOWNLOAD_FOLDER: download_folder},
    )


class CompletedTempCleanupTests(unittest.TestCase):
    def test_keeps_temp_directory_until_every_task_is_finished(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / YTDL_TEMP_DIR
            temp_dir.mkdir()
            (temp_dir / "video.part").write_bytes(b"partial")
            tasks = [
                make_task(1, TaskStatus.FINISHED, tmpdir),
                make_task(2, TaskStatus.PAUSED, tmpdir),
            ]

            removed = cleanup_temp_dirs_if_all_finished(tasks)

            self.assertEqual(removed, [])
            self.assertTrue(temp_dir.exists())

    def test_removes_temp_directory_and_part_files_when_all_tasks_are_finished(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_dir = Path(tmpdir) / YTDL_TEMP_DIR
            temp_dir.mkdir()
            (temp_dir / "stale.part").write_bytes(b"partial")
            tasks = [
                make_task(1, TaskStatus.FINISHED, tmpdir),
                make_task(2, TaskStatus.FINISHED, tmpdir),
            ]

            removed = cleanup_temp_dirs_if_all_finished(tasks)

            self.assertEqual(removed, [str(temp_dir)])
            self.assertFalse(temp_dir.exists())

    def test_removes_each_download_folder_only_once(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            first_temp = Path(first) / YTDL_TEMP_DIR
            second_temp = Path(second) / YTDL_TEMP_DIR
            first_temp.mkdir()
            second_temp.mkdir()
            tasks = [
                make_task(1, TaskStatus.FINISHED, first),
                make_task(2, TaskStatus.FINISHED, first),
                make_task(3, TaskStatus.FINISHED, second),
            ]

            removed = cleanup_temp_dirs_if_all_finished(tasks)

            self.assertCountEqual(removed, [str(first_temp), str(second_temp)])
            self.assertFalse(first_temp.exists())
            self.assertFalse(second_temp.exists())


if __name__ == "__main__":
    unittest.main()
