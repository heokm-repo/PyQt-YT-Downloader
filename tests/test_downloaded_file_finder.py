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

from core.download.file_finder import clean_title_for_match, find_downloaded_file


class DownloadedFileFinderTests(unittest.TestCase):
    def test_clean_title_for_match_keeps_word_characters_and_korean(self):
        self.assertEqual(clean_title_for_match("My 영상! 01"), "my영상01")

    def test_current_output_path_is_preferred_when_it_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            captured = Path(tmpdir) / "captured.webm"
            captured.write_text("", encoding="utf-8")
            other = Path(tmpdir) / "My Video.mp4"
            other.write_text("", encoding="utf-8")

            result = find_downloaded_file(str(captured), {"title": "My Video"}, tmpdir, task_id=7)

        self.assertEqual(result, str(captured.resolve()))

    def test_finds_matching_media_file_by_clean_title(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            match = Path(tmpdir) / "My Video (1080p).mp4"
            match.write_text("", encoding="utf-8")
            ignored = Path(tmpdir) / "My Video.txt"
            ignored.write_text("", encoding="utf-8")

            result = find_downloaded_file("", {"title": "My Video!"}, tmpdir)

        self.assertEqual(result, str(match.resolve()))

    def test_returns_empty_string_when_save_folder_is_missing(self):
        result = find_downloaded_file("", {"title": "Missing"}, "C:/definitely/missing/folder")

        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
