import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin import storage as bin_storage


class BinStorageTests(unittest.TestCase):
    def test_get_bin_path_creates_bin_directory_under_user_data_path(self):
        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(bin_storage, "get_user_data_path", return_value=tmpdir):
            path = Path(bin_storage.get_bin_path())

            self.assertEqual(path, Path(tmpdir) / "bin")
            self.assertTrue(path.is_dir())

    def test_binary_path_returns_only_existing_binary(self):
        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(bin_storage, "get_user_data_path", return_value=tmpdir):
            binary = Path(tmpdir) / "bin" / "tool.exe"
            binary.parent.mkdir()
            binary.write_text("bin", encoding="utf-8")

            self.assertEqual(bin_storage.binary_path("tool.exe"), str(binary))
            self.assertIsNone(bin_storage.binary_path("missing.exe"))

    def test_load_versions_file_returns_empty_for_missing_or_invalid_json(self):
        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(bin_storage, "get_user_data_path", return_value=tmpdir):
            self.assertEqual(bin_storage.load_versions_file(".version.json"), {})

            version_path = Path(bin_storage.version_file_path(".version.json"))
            version_path.write_text("not-json", encoding="utf-8")

            self.assertEqual(bin_storage.load_versions_file(".version.json"), {})

    def test_save_and_load_versions_file_drops_legacy_last_check(self):
        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(bin_storage, "get_user_data_path", return_value=tmpdir):
            saved = bin_storage.save_versions_file(
                {"yt-dlp": "2026.07.01", "last_check": "now"},
                ".version.json",
            )

            self.assertTrue(saved)
            self.assertEqual(
                bin_storage.load_versions_file(".version.json"),
                {"yt-dlp": "2026.07.01"},
            )

    def test_load_versions_file_migrates_legacy_last_check_on_disk(self):
        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(bin_storage, "get_user_data_path", return_value=tmpdir):
            version_path = Path(bin_storage.version_file_path(".version.json"))
            version_path.write_text(
                '{"yt-dlp": "2026.07.01", "last_check": "legacy"}',
                encoding="utf-8",
            )

            self.assertEqual(
                bin_storage.load_versions_file(".version.json"),
                {"yt-dlp": "2026.07.01"},
            )
            self.assertNotIn("last_check", version_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
