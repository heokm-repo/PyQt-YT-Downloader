import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.url_processor import UrlProcessor


class UrlProcessorTests(unittest.TestCase):
    def test_process_url_returns_none_for_invalid_url(self):
        self.assertIsNone(UrlProcessor.process_url("not a url"))

    def test_process_url_passes_through_non_youtube_url(self):
        result = UrlProcessor.process_url("https://example.test/video/123")

        self.assertEqual(result.clean_url, "https://example.test/video/123")
        self.assertFalse(result.is_playlist)
        self.assertIsNone(result.video_id)
        self.assertIsNone(result.extractor)

    def test_requires_playlist_preference_detects_youtube_video_with_list(self):
        url = "https://www.youtube.com/watch?v=abc12345678&list=PL123"

        self.assertTrue(UrlProcessor.requires_playlist_preference(url))

    def test_process_url_uses_playlist_preference(self):
        url = "https://www.youtube.com/watch?v=abc12345678&list=PL123"

        playlist_result = UrlProcessor.process_url(url, prefer_playlist=True)
        video_result = UrlProcessor.process_url(url, prefer_playlist=False)

        self.assertTrue(playlist_result.is_playlist)
        self.assertFalse(video_result.is_playlist)
        self.assertEqual(video_result.video_id, "abc12345678")


if __name__ == "__main__":
    unittest.main()