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

from utils.bin.install import (
    install_downloaded_binary,
    remove_if_exists,
    replace_existing_file,
    save_binary_version,
    version_record,
)


class BinInstallTests(unittest.TestCase):
    def test_version_record_sets_binary_and_removes_legacy_last_check(self):
        result = version_record(
            {"ffmpeg": "old", "last_check": "legacy"},
            "yt-dlp",
            "new",
        )

        self.assertEqual(result["ffmpeg"], "old")
        self.assertEqual(result["yt-dlp"], "new")
        self.assertNotIn("last_check", result)

    def test_remove_if_exists_removes_existing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "temp.bin"
            path.write_text("data", encoding="utf-8")

            removed = remove_if_exists(str(path))

            self.assertTrue(removed)
            self.assertFalse(path.exists())

    def test_remove_if_exists_noops_for_missing_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "missing.bin"

            self.assertFalse(remove_if_exists(str(path)))

    def test_replace_existing_file_replaces_existing_target(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.bin"
            target = Path(tmpdir) / "target.bin"
            source.write_text("new", encoding="utf-8")
            target.write_text("old", encoding="utf-8")

            replace_existing_file(str(source), str(target))

            self.assertFalse(source.exists())
            self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_save_binary_version_uses_load_and_save_callbacks(self):
        saved = []

        result = save_binary_version(
            "quickjs",
            "1.0",
            lambda: {"yt-dlp": "2024", "last_check": "legacy"},
            lambda versions: saved.append(versions) or True,
        )

        self.assertTrue(result)
        self.assertEqual(
            saved,
            [{"yt-dlp": "2024", "quickjs": "1.0"}],
        )

    def test_install_downloaded_binary_moves_file_and_saves_version(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_path = Path(tmpdir) / "tool.tmp"
            final_path = Path(tmpdir) / "tool.exe"
            temp_path.write_text("downloaded", encoding="utf-8")

            result = install_downloaded_binary(
                str(temp_path),
                str(final_path),
                "yt-dlp",
                "2026.07.01",
                lambda: {},
                lambda versions: saved.append(versions) or True,
            )

            self.assertTrue(result)
            self.assertFalse(temp_path.exists())
            self.assertEqual(final_path.read_text(encoding="utf-8"), "downloaded")

        self.assertEqual(saved[0]["yt-dlp"], "2026.07.01")
        self.assertNotIn("last_check", saved[0])


if __name__ == "__main__":
    unittest.main()
