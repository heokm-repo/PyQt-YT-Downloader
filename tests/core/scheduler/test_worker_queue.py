import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.worker_queue import parse_task_wrapper


class WorkerQueueTests(unittest.TestCase):
    def test_parse_generated_priority_task(self):
        task_data, mark_done = parse_task_wrapper(
            (1, 3, 10, "url", {"format": "mp4"}, {"title": "Video"}, True)
        )

        self.assertFalse(mark_done)
        self.assertEqual(task_data, (10, "url", {"format": "mp4"}, {"title": "Video"}, True, 3))

    def test_parse_shutdown_marker_requests_task_done(self):
        self.assertEqual(parse_task_wrapper((0, -1, None)), (None, True))

    def test_rejects_legacy_or_invalid_queue_entries(self):
        invalid_entries = (
            (0, None),
            (0, 0, None),
            (1, 10, "url", {"format": "mp4"}),
            (1, 10, "url", {"format": "mp4"}, {"title": "Video"}, True),
            (1, 10, "url", {"format": "mp4"}, {"title": "Video"}),
            [10, "url", {"format": "mp4"}, {"title": "Video"}],
            None,
        )
        for entry in invalid_entries:
            with self.subTest(entry=entry):
                with self.assertRaises(ValueError):
                    parse_task_wrapper(entry)


if __name__ == "__main__":
    unittest.main()
