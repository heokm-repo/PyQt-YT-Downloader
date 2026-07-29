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

from core.download import metadata_fetcher


class FakeMetadataWrapper:
    captured = {}

    def __init__(self, ytdlp_path):
        self.ytdlp_path = ytdlp_path

    def extract_info(self, url, options=None):
        self.captured["url"] = url
        self.captured["options"] = options
        return {
            "id": "abc123",
            "title": "Video",
            "extractor": "YouTube",
            "filesize": 50,
            "vcodec": "h264",
        }, True


class MetadataFetcherTests(unittest.TestCase):
    def test_fetch_metadata_maps_info_and_passes_extract_options(self):
        FakeMetadataWrapper.captured = {}
        with patch.object(metadata_fetcher, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(metadata_fetcher, "YtDlpWrapper", FakeMetadataWrapper):
            metadata, success = metadata_fetcher.fetch_metadata(
                "https://www.youtube.com/watch?v=abc123&list=playlist456",
                {"format": "mp4", "video_quality": "best"},
            )

        self.assertTrue(success)
        self.assertEqual(metadata["id"], "abc123")
        self.assertEqual(metadata["title"], "Video")
        self.assertEqual(metadata["extractor"], "youtube")
        self.assertEqual(FakeMetadataWrapper.captured["url"], "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(FakeMetadataWrapper.captured["options"]["extract_flat"], "in_playlist")
        self.assertTrue(FakeMetadataWrapper.captured["options"]["noplaylist"])

    def test_fetch_metadata_returns_false_without_ytdlp(self):
        with patch.object(metadata_fetcher, "get_ytdlp_path", return_value=None):
            metadata, success = metadata_fetcher.fetch_metadata("https://example.invalid/video")

        self.assertFalse(success)
        self.assertEqual(metadata, {})


if __name__ == "__main__":
    unittest.main()
