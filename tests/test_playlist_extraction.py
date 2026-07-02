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

from core.download import playlist_extractor


class FakePlaylistWrapper:
    def __init__(self, ytdlp_path):
        self.ytdlp_path = ytdlp_path

    def extract_info(self, url, download=False, options=None):
        return {
            "_type": "playlist",
            "entries": [
                {"id": "one"},
                {"url": "https://www.youtube.com/watch?v=two"},
                {},
            ],
        }, True


class PlaylistExtractionTests(unittest.TestCase):
    def test_extract_playlist_video_ids_filters_empty_entries(self):
        with patch.object(playlist_extractor, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(playlist_extractor, "YtDlpWrapper", FakePlaylistWrapper):
            ids, success, error = playlist_extractor.extract_playlist_video_ids(
                "https://www.youtube.com/playlist?list=playlist123"
            )

        self.assertTrue(success)
        self.assertEqual(error, "")
        self.assertEqual(ids, ["one", "two"])

    def test_extract_entry_ids_handles_missing_values(self):
        self.assertEqual(
            playlist_extractor.extract_entry_ids([
                {"id": "one"},
                {"url": "https://www.youtube.com/watch?v=two"},
                {"url": ""},
                {},
                None,
            ]),
            ["one", "two"],
        )


if __name__ == "__main__":
    unittest.main()
