import os
import queue
import sys
import threading
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.scheduler import DownloadScheduler
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

    def test_cancelled_running_task_triggers_stop_check(self):
        generation = self.scheduler.add_task(1, 30, "url", {"format": "mp4"}, {}, is_resume=False)
        self.worker.current_task_id = 30
        self.worker.current_generation = generation

        self.assertFalse(self.worker._stop_check())

        self.scheduler.cancel_task(30)

        self.assertTrue(self.worker._stop_check())

    def test_worker_combines_video_and_audio_progress(self):
        emitted = []
        self.worker.progress_updated.connect(lambda data, task_id: emitted.append((data.copy(), task_id)))
        self.worker.download_progress[40] = {
            "video": {"downloaded": 100, "total": 100, "filename": "video.mp4"},
            "audio": {"downloaded": 0, "total": 50, "filename": "audio.webm"},
            "postprocessing": False,
            "total_size_est": 150,
            "video_size_est": 100,
            "audio_size_est": 50,
        }
        self.worker.last_update_times[40] = 0.0

        self.worker._handle_downloading_status(
            {
                "status": "downloading",
                "filename": "audio.webm",
                "downloaded_bytes": 25,
                "total_bytes": 50,
                "speed": 1024,
            },
            40,
        )

        self.assertEqual(len(emitted), 1)
        data, task_id = emitted[0]
        self.assertEqual(task_id, 40)
        self.assertEqual(data["downloaded_bytes"], 125)
        self.assertEqual(data["total_bytes"], 150)
        self.assertEqual(data["_percent_str"], "83.3%")
    def test_shutdown_marker_is_parsed_as_no_task(self):
        self.scheduler.download_queue.put((0, -1, None))
        entry = self.scheduler.download_queue.get_nowait()

        self.assertIsNone(self.worker._extract_task_data(entry))


if __name__ == "__main__":
    unittest.main()
