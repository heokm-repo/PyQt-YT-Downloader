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
            opts = download_options._build_playlist_extract_options(
                url="https://www.youtube.com/playlist?list=playlist123"
            )

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
                url="https://www.youtube.com/watch?v=video123",
            )

        self.assertEqual(opts["extract_flat"], "in_playlist")
        self.assertTrue(opts["noplaylist"])
        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertNotIn("audio_format", opts)
        self.assertEqual(opts["cookiefile"], "cookies.txt")

    def test_advanced_options_add_cookies_only_for_youtube_urls(self):
        with patch("utils.cookie_store.cookie_file_exists", return_value=True), \
             patch("utils.cookie_store.get_cookie_file_path", return_value="cookies.txt"):
            youtube_opts = download_options._build_advanced_options(
                {},
                "https://www.youtube.com/watch?v=video123",
            )
            other_site_opts = download_options._build_advanced_options(
                {},
                "https://example.test/video123",
            )

        self.assertEqual(youtube_opts["cookiefile"], "cookies.txt")
        self.assertNotIn("cookiefile", other_site_opts)


if __name__ == "__main__":
    unittest.main()
