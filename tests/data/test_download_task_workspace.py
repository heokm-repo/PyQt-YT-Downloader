import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from data.models import DownloadTask


class DownloadTaskWorkspaceTests(unittest.TestCase):
    def test_same_media_tasks_receive_distinct_case_safe_workspace_ids(self):
        first = DownloadTask(
            id=1,
            url="https://example.test/Video",
            video_id="CaseSensitive-ID",
            extractor="Example",
        )
        second = DownloadTask(
            id=2,
            url="https://example.test/Video",
            video_id="CaseSensitive-ID",
            extractor="Example",
        )

        self.assertEqual(len(first.workspace_id), 32)
        self.assertEqual(len(second.workspace_id), 32)
        self.assertNotEqual(first.workspace_id, second.workspace_id)

    def test_workspace_id_round_trips_without_changing(self):
        task = DownloadTask(id=1, url="https://example.test/video")

        restored = DownloadTask.from_dict(task.to_dict())

        self.assertEqual(restored.workspace_id, task.workspace_id)
        self.assertFalse(restored.legacy_workspace)

    def test_legacy_task_receives_uuid_and_keeps_migration_flag(self):
        restored = DownloadTask.from_dict(
            {
                "id": 1,
                "url": "https://example.test/video",
                "status": "paused",
            }
        )

        self.assertEqual(len(restored.workspace_id), 32)
        self.assertTrue(restored.legacy_workspace)
        persisted = DownloadTask.from_dict(restored.to_dict())
        self.assertEqual(persisted.workspace_id, restored.workspace_id)
        self.assertTrue(persisted.legacy_workspace)


if __name__ == "__main__":
    unittest.main()
