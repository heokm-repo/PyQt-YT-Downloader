import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin import manager as bin_manager


class BinManagerReleaseChecksTests(unittest.TestCase):
    def test_check_ytdlp_latest_version_delegates_release_check(self):
        with patch.object(
            bin_manager,
            "check_latest_github_release",
            return_value=(
                "2026.07.01",
                "https://example.test/yt-dlp.exe",
                "sha256:" + "a" * 64,
            ),
        ) as release_check:
            result = bin_manager.check_ytdlp_latest_version()

        self.assertEqual(
            result,
            (
                "2026.07.01",
                "https://example.test/yt-dlp.exe",
                "sha256:" + "a" * 64,
            ),
        )
        self.assertEqual(release_check.call_args.args[0], bin_manager.YTDLP_API_URL)
        self.assertEqual(release_check.call_args.args[1], "yt-dlp")

    def test_check_ffmpeg_latest_version_delegates_release_check(self):
        with patch.object(
            bin_manager,
            "check_latest_github_release",
            return_value=(None, None, None),
        ) as release_check:
            result = bin_manager.check_ffmpeg_latest_version()

        self.assertEqual(result, (None, None, None))
        self.assertEqual(release_check.call_args.args[0], bin_manager.FFMPEG_API_URL)
        self.assertEqual(release_check.call_args.args[1], "ffmpeg")


if __name__ == "__main__":
    unittest.main()
