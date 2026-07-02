import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.tasks.task_file_delete import DeleteFileStatus, delete_output_file


class TaskFileDeleteTests(unittest.TestCase):
    def test_delete_output_file_without_path_returns_no_path(self):
        result = delete_output_file("")

        self.assertEqual(result.status, DeleteFileStatus.NO_PATH)
        self.assertEqual(result.output_path, "")

    def test_delete_output_file_removes_existing_file(self):
        removed_paths = []
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = delete_output_file(str(file_path), removed_paths.append)

        self.assertEqual(result.status, DeleteFileStatus.DELETED)
        self.assertEqual(result.file_path, str(file_path))
        self.assertEqual(removed_paths, [str(file_path)])

    def test_delete_output_file_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.mp4"

            result = delete_output_file(str(missing_path))

        self.assertEqual(result.status, DeleteFileStatus.MISSING)
        self.assertEqual(result.output_path, str(missing_path))

    def test_delete_output_file_reports_existing_non_file_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = delete_output_file(tmpdir)

        self.assertEqual(result.status, DeleteFileStatus.NOT_FILE)
        self.assertEqual(result.output_path, tmpdir)

    def test_delete_output_file_reports_permission_errors(self):
        error = PermissionError("locked")

        def raise_permission_error(_path):
            raise error

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = delete_output_file(str(file_path), raise_permission_error)

        self.assertEqual(result.status, DeleteFileStatus.PERMISSION_ERROR)
        self.assertIs(result.error, error)
        self.assertIsNotNone(result.exc_info)

    def test_delete_output_file_reports_generic_errors(self):
        error = RuntimeError("boom")

        def raise_error(_path):
            raise error

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = delete_output_file(str(file_path), raise_error)

        self.assertEqual(result.status, DeleteFileStatus.ERROR)
        self.assertIs(result.error, error)


if __name__ == "__main__":
    unittest.main()
