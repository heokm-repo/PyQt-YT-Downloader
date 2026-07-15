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

from core.youtube_url import _sanitize_url, extract_video_id, has_video_and_list
from utils.utils import is_youtube_url


class YoutubeUrlTests(unittest.TestCase):
    def test_youtube_host_detection_uses_hostname_boundaries(self):
        self.assertTrue(is_youtube_url("https://www.youtube.com/watch?v=video123"))
        self.assertTrue(is_youtube_url("https://music.youtube.com/watch?v=video123"))
        self.assertTrue(is_youtube_url("https://youtu.be/video123"))
        self.assertFalse(is_youtube_url("https://youtube.com.example.test/watch?v=video123"))
        self.assertFalse(is_youtube_url("https://example.test/?next=https://youtube.com/watch?v=video123"))

    def test_video_playlist_url_defaults_to_single_video(self):
        clean_url, is_playlist = _sanitize_url(
            "https://www.youtube.com/watch?v=video123&list=playlist456&index=2"
        )

        self.assertFalse(is_playlist)
        self.assertEqual(clean_url, "https://www.youtube.com/watch?v=video123&index=2")

    def test_video_playlist_url_can_prefer_playlist(self):
        clean_url, is_playlist = _sanitize_url(
            "https://www.youtube.com/watch?v=video123&list=playlist456",
            prefer_playlist=True,
        )

        self.assertTrue(is_playlist)
        self.assertEqual(clean_url, "https://www.youtube.com/playlist?list=playlist456")

    def test_youtu_be_playlist_url_counts_as_video_and_playlist(self):
        url = "https://youtu.be/video123?list=playlist456"

        self.assertTrue(has_video_and_list(url))

    def test_shorts_url_is_not_treated_as_playlist_choice(self):
        url = "https://www.youtube.com/shorts/video123?list=playlist456"

        self.assertFalse(has_video_and_list(url))
        self.assertEqual(_sanitize_url(url), (url, False))

    def test_extract_video_id_from_watch_url(self):
        self.assertEqual(
            extract_video_id("https://www.youtube.com/watch?v=video123&feature=share"),
            "video123",
        )

    def test_extract_video_id_from_short_url(self):
        self.assertEqual(extract_video_id("https://youtu.be/video123"), "video123")

    def test_extract_video_id_ignores_non_youtube_url(self):
        self.assertIsNone(extract_video_id("https://example.invalid/watch?v=video123"))

    def test_non_youtube_url_is_returned_unchanged(self):
        url = "https://example.invalid/watch?v=video123&list=playlist456"

        self.assertFalse(has_video_and_list(url))
        self.assertEqual(_sanitize_url(url), (url, False))


if __name__ == "__main__":
    unittest.main()
