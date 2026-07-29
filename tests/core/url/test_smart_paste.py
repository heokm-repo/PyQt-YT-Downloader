import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.main_window.smart_paste import extract_valid_clipboard_url


class SmartPasteTests(unittest.TestCase):
    def test_extract_valid_clipboard_url_strips_valid_url(self):
        self.assertEqual(
            extract_valid_clipboard_url("  https://example.invalid/video  "),
            "https://example.invalid/video",
        )

    def test_extract_valid_clipboard_url_rejects_blank_or_invalid_text(self):
        self.assertEqual(extract_valid_clipboard_url(""), "")
        self.assertEqual(extract_valid_clipboard_url(None), "")
        self.assertEqual(extract_valid_clipboard_url("not a url"), "")
        self.assertEqual(extract_valid_clipboard_url("ftp://example.invalid/file"), "")


if __name__ == "__main__":
    unittest.main()