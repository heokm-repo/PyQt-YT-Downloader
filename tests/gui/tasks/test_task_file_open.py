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

from gui.tasks.task_file_open import (
    OpenFileStatus,
    OpenFolderStatus,
    open_output_file,
    open_output_folder,
)


class TaskFileOpenTests(unittest.TestCase):
    def test_open_output_file_without_path_returns_no_path(self):
        result = open_output_file("")

        self.assertEqual(result.status, OpenFileStatus.NO_PATH)

    def test_open_output_file_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.mp4"

            result = open_output_file(str(missing_path))

        self.assertEqual(result.status, OpenFileStatus.MISSING)
        self.assertEqual(result.output_path, str(missing_path))

    def test_open_output_file_opens_existing_file(self):
        opened_paths = []
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = open_output_file(str(file_path), opened_paths.append)

        self.assertEqual(result.status, OpenFileStatus.OPENED)
        self.assertEqual(result.file_path, str(file_path))
        self.assertEqual(opened_paths, [str(file_path)])

    def test_open_output_file_reports_open_errors(self):
        error = RuntimeError("cannot open")

        def raise_error(_path):
            raise error

        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = open_output_file(str(file_path), raise_error)

        self.assertEqual(result.status, OpenFileStatus.ERROR)
        self.assertIs(result.error, error)

    def test_open_output_folder_opens_parent_of_existing_file(self):
        opened_paths = []
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("data", encoding="utf-8")

            result = open_output_folder(str(file_path), opened_paths.append)

        self.assertEqual(result.status, OpenFolderStatus.OPENED)
        self.assertFalse(result.select_file)
        self.assertEqual(opened_paths, [str(file_path.parent)])

    def test_open_output_folder_opens_existing_parent_for_missing_file(self):
        opened_paths = []
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.mp4"

            result = open_output_folder(str(missing_path), opened_paths.append)

        self.assertEqual(result.status, OpenFolderStatus.OPENED)
        self.assertFalse(result.select_file)
        self.assertEqual(result.path, str(missing_path.parent))
        self.assertEqual(opened_paths, [str(missing_path.parent)])

    def test_open_output_folder_without_target_returns_no_target(self):
        result = open_output_folder("")

        self.assertEqual(result.status, OpenFolderStatus.NO_TARGET)

    def test_open_output_folder_reports_errors(self):
        error = RuntimeError("folder failed")

        def raise_error(_path):
            raise error

        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.mp4"

            result = open_output_folder(str(missing_path), raise_error)

        self.assertEqual(result.status, OpenFolderStatus.ERROR)
        self.assertIs(result.error, error)


if __name__ == "__main__":
    unittest.main()
