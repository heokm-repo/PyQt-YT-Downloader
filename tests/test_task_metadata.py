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

from core.task_metadata import apply_metadata_to_task
from data.models import DownloadTask


class TaskMetadataTests(unittest.TestCase):
    def test_metadata_fills_missing_video_id_and_extractor(self):
        task = DownloadTask(
            id=1,
            url="https://example.invalid/video",
            video_id=None,
            extractor="unknown",
        )
        metadata = {"id": "abc123", "extractor": "YouTube", "title": "Example"}

        apply_metadata_to_task(task, metadata)

        self.assertIs(task.meta, metadata)
        self.assertEqual(task.video_id, "abc123")
        self.assertEqual(task.extractor, "youtube")

    def test_metadata_preserves_existing_identity(self):
        task = DownloadTask(
            id=1,
            url="https://example.invalid/video",
            video_id="existing",
            extractor="vimeo",
        )
        metadata = {"id": "abc123", "extractor": "YouTube"}

        apply_metadata_to_task(task, metadata)

        self.assertEqual(task.video_id, "existing")
        self.assertEqual(task.extractor, "vimeo")

    def test_missing_extractor_defaults_empty_task_to_unknown(self):
        task = DownloadTask(
            id=1,
            url="https://example.invalid/video",
            extractor="",
        )

        apply_metadata_to_task(task, {"id": "abc123"})

        self.assertEqual(task.extractor, "unknown")


if __name__ == "__main__":
    unittest.main()
