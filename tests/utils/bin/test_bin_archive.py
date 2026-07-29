import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin.archive import extract_zip_member_ending_with


class BinArchiveTests(unittest.TestCase):
    def test_extract_zip_member_ending_with_extracts_first_matching_member(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "archive.zip"
            dest_path = Path(tmpdir) / "ffmpeg.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("docs/readme.txt", "ignored")
                archive.writestr("build/bin/ffmpeg.exe", b"binary")

            extracted = extract_zip_member_ending_with(
                str(zip_path),
                str(dest_path),
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
            )

            self.assertTrue(extracted)
            self.assertEqual(dest_path.read_bytes(), b"binary")

    def test_extract_zip_member_ending_with_returns_false_without_match(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "archive.zip"
            dest_path = Path(tmpdir) / "ffmpeg.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("docs/readme.txt", "ignored")

            extracted = extract_zip_member_ending_with(
                str(zip_path),
                str(dest_path),
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
            )

            self.assertFalse(extracted)
            self.assertFalse(dest_path.exists())


if __name__ == "__main__":
    unittest.main()