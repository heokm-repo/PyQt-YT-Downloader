import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import main
from utils.bin import manager as bin_manager
from constants import FFMPEG_ZIP_NAME_WIN


class WindowsPolicyTests(unittest.TestCase):
    def test_main_accepts_only_win32_platform(self):
        self.assertTrue(main.is_supported_platform("win32"))
        self.assertFalse(main.is_supported_platform("linux"))
        self.assertFalse(main.is_supported_platform("darwin"))

    def test_binary_assets_are_windows_only(self):
        self.assertEqual(bin_manager.YTDLP_BINARY, "yt-dlp.exe")
        self.assertEqual(bin_manager.FFMPEG_BINARY, "ffmpeg.exe")
        self.assertEqual(bin_manager.QUICKJS_BINARY, "qjs.exe")
        self.assertEqual(bin_manager.QUICKJS_ASSET_NAME, "qjs-windows-x86_64.exe")
        self.assertEqual(FFMPEG_ZIP_NAME_WIN, "ffmpeg-master-latest-win64-gpl.zip")


if __name__ == "__main__":
    unittest.main()
