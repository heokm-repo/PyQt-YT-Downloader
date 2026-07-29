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

from core.download.output_paths import verified_download_output_path
from gui.tasks.task_file_paths import (
    existing_file_path,
    existing_parent_folder,
    normalize_output_path,
    resolve_open_folder_target,
)


class TaskFilePathsTests(unittest.TestCase):
    def test_normalize_output_path_handles_missing_and_relative_paths(self):
        self.assertEqual(normalize_output_path(""), "")
        self.assertTrue(os.path.isabs(normalize_output_path("relative-file.mp4")))

    def test_existing_file_path_returns_only_existing_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("", encoding="utf-8")
            dir_path = Path(tmpdir) / "folder"
            dir_path.mkdir()

            self.assertEqual(existing_file_path(str(file_path)), str(file_path))
            self.assertEqual(existing_file_path(str(dir_path)), "")
            self.assertEqual(existing_file_path(str(Path(tmpdir) / "missing.mp4")), "")

    def test_resolve_open_folder_target_uses_parent_of_existing_output_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "video.mp4"
            file_path.write_text("", encoding="utf-8")

            target = resolve_open_folder_target(str(file_path))

        self.assertEqual(target.path, str(file_path.parent))
        self.assertFalse(target.select_file)

    def test_resolve_open_folder_target_falls_back_to_existing_parent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_path = Path(tmpdir) / "missing.mp4"

            target = resolve_open_folder_target(str(missing_path))

        self.assertEqual(target.path, str(missing_path.parent))
        self.assertFalse(target.select_file)

    def test_existing_parent_folder_returns_parent_only_when_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            self.assertEqual(existing_parent_folder(str(Path(tmpdir) / "video.mp4")), tmpdir)

        self.assertEqual(existing_parent_folder(""), "")

    def test_verified_download_output_accepts_existing_file_inside_download_folder(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "video.webm"
            output.write_bytes(b"media")

            self.assertEqual(
                verified_download_output_path(str(output), tmpdir),
                str(output.resolve()),
            )

    def test_verified_download_output_rejects_missing_outside_and_temporary_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir) / "downloads"
            root.mkdir()
            outside = Path(tmpdir) / "outside.mp4"
            outside.write_bytes(b"outside")
            temporary = root / ".ytdl_temp" / "partial.webm"
            temporary.parent.mkdir()
            temporary.write_bytes(b"partial")

            self.assertEqual(
                verified_download_output_path(str(root / "missing.mp4"), str(root)),
                "",
            )
            self.assertEqual(
                verified_download_output_path(str(outside), str(root)),
                "",
            )
            self.assertEqual(
                verified_download_output_path(str(temporary), str(root)),
                "",
            )


if __name__ == "__main__":
    unittest.main()
