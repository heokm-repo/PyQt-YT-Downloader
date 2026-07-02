import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download import options as download_options


class DownloadExtractOptionTests(unittest.TestCase):
    def test_playlist_extract_options_include_only_runtime_advanced_options(self):
        with patch.object(
            download_options,
            "_build_advanced_options",
            return_value={
                "cookiefile": "cookies.txt",
                "js_runtimes": "quickjs:qjs.exe",
                "concurrent_fragment_downloads": 6,
            },
        ):
            opts = download_options._build_playlist_extract_options()

        self.assertEqual(opts, {
            "extract_flat": True,
            "cookiefile": "cookies.txt",
            "js_runtimes": "quickjs:qjs.exe",
        })

    def test_metadata_extract_options_include_format_and_runtime_options(self):
        with patch.object(
            download_options,
            "_build_advanced_options",
            return_value={"cookiefile": "cookies.txt"},
        ):
            opts = download_options._build_metadata_extract_options(
                {"format": "mp3", "audio_quality": "best"},
                is_playlist=False,
            )

        self.assertEqual(opts["extract_flat"], "in_playlist")
        self.assertTrue(opts["noplaylist"])
        self.assertEqual(opts["audio_format"], "mp3")
        self.assertEqual(opts["cookiefile"], "cookies.txt")


if __name__ == "__main__":
    unittest.main()
