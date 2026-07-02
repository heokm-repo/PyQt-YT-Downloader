import os
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin.install import (
    install_downloaded_binary,
    last_check_record,
    remove_if_exists,
    replace_existing_file,
    save_binary_version,
    save_last_check,
    version_record_with_check,
)


class BinInstallTests(unittest.TestCase):
    def test_version_record_with_check_sets_binary_and_timestamp(self):
        checked_at = datetime(2026, 7, 1, 10, 0, 0)

        result = version_record_with_check({"ffmpeg": "old"}, "yt-dlp", "new", checked_at)

        self.assertEqual(result["ffmpeg"], "old")
        self.assertEqual(result["yt-dlp"], "new")
        self.assertEqual(result["last_check"], "2026-07-01T10:00:00")

    def test_last_check_record_sets_timestamp_without_changing_versions(self):
        checked_at = datetime(2026, 7, 1, 10, 0, 0)

        result = last_check_record({"yt-dlp": "2024"}, checked_at)

        self.assertEqual(result, {"yt-dlp": "2024", "last_check": "2026-07-01T10:00:00"})

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
        checked_at = datetime(2026, 7, 1, 10, 0, 0)

        result = save_binary_version(
            "quickjs",
            "1.0",
            lambda: {"yt-dlp": "2024"},
            lambda versions: saved.append(versions) or True,
            checked_at,
        )

        self.assertTrue(result)
        self.assertEqual(
            saved,
            [{"yt-dlp": "2024", "quickjs": "1.0", "last_check": "2026-07-01T10:00:00"}],
        )

    def test_save_last_check_uses_load_and_save_callbacks(self):
        saved = []
        checked_at = datetime(2026, 7, 1, 10, 0, 0)

        result = save_last_check(
            lambda: {"yt-dlp": "2024"},
            lambda versions: saved.append(versions) or True,
            checked_at,
        )

        self.assertTrue(result)
        self.assertEqual(saved, [{"yt-dlp": "2024", "last_check": "2026-07-01T10:00:00"}])

    def test_install_downloaded_binary_moves_file_and_saves_version(self):
        saved = []
        checked_at = datetime(2026, 7, 1, 10, 0, 0)
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
                checked_at,
            )

            self.assertTrue(result)
            self.assertFalse(temp_path.exists())
            self.assertEqual(final_path.read_text(encoding="utf-8"), "downloaded")

        self.assertEqual(saved[0]["yt-dlp"], "2026.07.01")
        self.assertEqual(saved[0]["last_check"], "2026-07-01T10:00:00")


if __name__ == "__main__":
    unittest.main()