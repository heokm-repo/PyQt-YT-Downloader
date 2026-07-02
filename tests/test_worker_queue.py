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

from core.worker_queue import parse_task_wrapper


class WorkerQueueTests(unittest.TestCase):
    def test_parse_generated_priority_task(self):
        task_data, mark_done = parse_task_wrapper(
            (1, 3, 10, "url", {"format": "mp4"}, {"title": "Video"}, True)
        )

        self.assertFalse(mark_done)
        self.assertEqual(task_data, (10, "url", {"format": "mp4"}, {"title": "Video"}, True, 3))

    def test_parse_priority_task_without_generation(self):
        task_data, mark_done = parse_task_wrapper(
            (1, 10, "url", {"format": "mp4"}, {"title": "Video"}, True)
        )

        self.assertFalse(mark_done)
        self.assertEqual(task_data, (10, "url", {"format": "mp4"}, {"title": "Video"}, True, None))

    def test_parse_legacy_sequence_task(self):
        task_data, mark_done = parse_task_wrapper([10, "url", {"format": "mp4"}, {"title": "Video"}])

        self.assertFalse(mark_done)
        self.assertEqual(task_data, (10, "url", {"format": "mp4"}, {"title": "Video"}, False, None))

    def test_parse_shutdown_markers_request_task_done(self):
        self.assertEqual(parse_task_wrapper((0, None)), (None, True))
        self.assertEqual(parse_task_wrapper((0, -1, None)), (None, True))

    def test_none_task_is_ignored_without_task_done(self):
        self.assertEqual(parse_task_wrapper(None), (None, False))


if __name__ == "__main__":
    unittest.main()
