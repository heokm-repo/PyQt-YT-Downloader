import os
import queue
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.scheduler import DownloadScheduler
from core.download.result import DownloadResult
from core.workers import DownloadWorker


class SchedulerWorkerControlTests(unittest.TestCase):
    def setUp(self):
        self.scheduler = DownloadScheduler()
        self.worker = DownloadWorker(
            self.scheduler.download_queue,
            self.scheduler.stop_event,
            self.scheduler.pause_event,
            self.scheduler,
        )

    def _next_task_data(self):
        entry = self.scheduler.download_queue.get_nowait()
        return self.worker._extract_task_data(entry)

    def _run_single_task(self, task_id, url, settings, metadata, fake_download):
        self.scheduler.add_task(1, task_id, url, settings, metadata)
        with patch(
            "core.workers.download_handler.download_video_with_result",
            side_effect=fake_download,
        ):
            self.worker.run()

    def test_newer_resume_generation_makes_older_queue_entry_stale(self):
        first_generation = self.scheduler.add_task(1, 10, "url", {"format": "mp4"}, {}, is_resume=True)
        second_generation = self.scheduler.add_task(1, 10, "url", {"format": "mp4"}, {}, is_resume=True)

        self.assertEqual(first_generation, 1)
        self.assertEqual(second_generation, 2)

        first_task = self._next_task_data()
        self.assertEqual(first_task[0], 10)
        self.assertEqual(first_task[5], 1)
        self.assertTrue(self.worker._should_skip_task(first_task[0], first_task[5]))

        second_task = self._next_task_data()
        self.assertEqual(second_task[5], 2)
        self.assertFalse(self.worker._should_skip_task(second_task[0], second_task[5]))

    def test_cancelled_task_is_skipped_before_start(self):
        self.scheduler.add_task(1, 20, "url", {"format": "mp4"}, {}, is_resume=False)
        self.scheduler.cancel_task(20)

        task = self._next_task_data()

        self.assertTrue(self.worker._should_skip_task(task[0], task[5]))

    def test_cancel_between_skip_check_and_claim_cannot_start_task(self):
        self.scheduler.add_task(
            1,
            21,
            "url",
            {"format": "mp4"},
            {},
            is_resume=False,
        )
        task = self._next_task_data()

        self.assertFalse(self.worker._should_skip_task(task[0], task[5]))
        self.scheduler.cancel_task(21)

        self.assertFalse(self.worker._claim_task(task[0], task[5]))
        self.assertFalse(self.scheduler.is_task_running(21))

    def test_cancelled_claim_remains_running_until_worker_releases_it(self):
        generation = self.scheduler.add_task(
            1,
            22,
            "url",
            {"format": "mp4"},
            {},
            is_resume=False,
        )

        self.assertTrue(self.scheduler.claim_task(22, generation))
        self.scheduler.cancel_task(22)

        self.assertTrue(self.scheduler.is_task_running(22))
        self.scheduler.release_task(22, generation)
        self.assertFalse(self.scheduler.is_task_running(22))

    def test_cancelled_running_task_triggers_stop_check(self):
        generation = self.scheduler.add_task(1, 30, "url", {"format": "mp4"}, {}, is_resume=False)
        self.worker.current_task_id = 30
        self.worker.current_generation = generation

        self.assertFalse(self.worker._stop_check())

        self.scheduler.cancel_task(30)

        self.assertTrue(self.worker._stop_check())

    def test_shutdown_marker_is_parsed_as_no_task(self):
        self.scheduler.download_queue.put((0, -1, None))
        entry = self.scheduler.download_queue.get_nowait()

        self.assertIsNone(self.worker._extract_task_data(entry))


if __name__ == "__main__":
    unittest.main()
