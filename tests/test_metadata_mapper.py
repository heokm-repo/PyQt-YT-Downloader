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

from core.download.metadata_mapper import build_metadata_result, estimate_media_sizes


class MetadataMapperTests(unittest.TestCase):
    def test_playlist_metadata_uses_playlist_defaults_and_count(self):
        metadata = build_metadata_result(
            {
                "_type": "playlist",
                "entries": [{"id": "one"}, {"id": "two"}],
                "extractor_key": "YouTube",
            },
            "https://www.youtube.com/playlist?list=abc",
            is_playlist=True,
        )

        self.assertEqual(metadata["title"], "PlayList")
        self.assertEqual(metadata["uploader"], "Unknown")
        self.assertTrue(metadata["is_playlist"])
        self.assertEqual(metadata["video_count"], 2)
        self.assertEqual(metadata["extractor"], "youtube")

    def test_single_video_metadata_uses_requested_format_sizes(self):
        metadata = build_metadata_result(
            {
                "title": "Video",
                "channel": "Channel",
                "duration": 12,
                "id": "abc123",
                "extractor": "YouTube",
                "requested_formats": [
                    {"vcodec": "h264", "acodec": "none", "filesize": 100},
                    {"vcodec": "none", "acodec": "aac", "filesize_approx": 25},
                ],
            },
            "https://example.invalid/video",
            is_playlist=False,
        )

        self.assertEqual(metadata["title"], "Video")
        self.assertEqual(metadata["uploader"], "Channel")
        self.assertEqual(metadata["duration"], 12)
        self.assertEqual(metadata["id"], "abc123")
        self.assertEqual(metadata["extractor"], "youtube")
        self.assertEqual(metadata["video_size"], 100)
        self.assertEqual(metadata["audio_size"], 25)
        self.assertEqual(metadata["webpage_url"], "https://example.invalid/video")

    def test_entries_use_first_entry_and_entry_extractor(self):
        metadata = build_metadata_result(
            {
                "extractor": "Generic",
                "entries": [
                    {
                        "id": "first",
                        "title": "First",
                        "extractor_key": "YouTube",
                        "webpage_url": "https://www.youtube.com/watch?v=first",
                    }
                ],
            },
            "https://www.youtube.com/watch?v=outer",
            is_playlist=False,
        )

        self.assertEqual(metadata["id"], "first")
        self.assertEqual(metadata["title"], "First")
        self.assertEqual(metadata["extractor"], "youtube")
        self.assertEqual(metadata["webpage_url"], "https://www.youtube.com/watch?v=first")

    def test_media_size_falls_back_to_available_formats(self):
        video_size, audio_size = estimate_media_sizes({
            "formats": [
                {"vcodec": "h264", "acodec": "none", "filesize": 90},
                {"vcodec": "vp9", "acodec": "none", "filesize_approx": 120},
                {"vcodec": "none", "acodec": "opus", "filesize": 15},
                {"vcodec": "none", "acodec": "aac", "filesize_approx": 25},
            ]
        })

        self.assertEqual(video_size, 120)
        self.assertEqual(audio_size, 25)


if __name__ == "__main__":
    unittest.main()
