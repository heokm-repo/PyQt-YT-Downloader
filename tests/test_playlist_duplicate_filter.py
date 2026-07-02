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

from constants import TaskStatus
from core.playlist_filter import filter_duplicate_videos
from data.models import DownloadTask


class FakeHistoryManager:
    def __init__(self, downloaded):
        self.downloaded = set(downloaded)

    def is_downloaded(self, extractor, video_id, target_format):
        return (extractor, video_id, target_format) in self.downloaded


class PlaylistDuplicateFilterTests(unittest.TestCase):
    def test_history_duplicate_only_matches_same_format(self):
        history_manager = FakeHistoryManager({("youtube", "same", "mkv")})
        tasks = []

        filtered, duplicate_count = filter_duplicate_videos(
            ["same"],
            history_manager,
            tasks,
            extractor="youtube",
            target_format="mp4",
        )

        self.assertEqual(filtered, ["same"])
        self.assertEqual(duplicate_count, 0)

        filtered, duplicate_count = filter_duplicate_videos(
            ["same"],
            history_manager,
            tasks,
            extractor="youtube",
            target_format="mkv",
        )

        self.assertEqual(filtered, [])
        self.assertEqual(duplicate_count, 1)

    def test_queue_duplicate_only_matches_same_format(self):
        history_manager = FakeHistoryManager(set())
        tasks = [
            DownloadTask(
                id=1,
                url="https://example.invalid/video",
                status=TaskStatus.WAITING,
                video_id="same",
                extractor="youtube",
                settings={"format": "mkv"},
            )
        ]

        filtered, duplicate_count = filter_duplicate_videos(
            ["same"],
            history_manager,
            tasks,
            extractor="youtube",
            target_format="mp4",
        )

        self.assertEqual(filtered, ["same"])
        self.assertEqual(duplicate_count, 0)

        filtered, duplicate_count = filter_duplicate_videos(
            ["same"],
            history_manager,
            tasks,
            extractor="youtube",
            target_format="mkv",
        )

        self.assertEqual(filtered, [])
        self.assertEqual(duplicate_count, 1)


if __name__ == "__main__":
    unittest.main()
