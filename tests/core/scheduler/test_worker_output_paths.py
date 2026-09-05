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

    def test_worker_does_not_provide_title_based_output_fallback(self):
        task_id = 75

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(
                _url,
                _settings,
                _progress_hook,
                is_resume=False,
                stop_check=None,
                metadata_hook=None,
                output_path_fallback=None,
            ):
                self.assertFalse(is_resume)
                self.assertTrue(callable(stop_check))
                self.assertTrue(callable(metadata_hook))
                self.assertIsNone(output_path_fallback)
                metadata_hook(
                    {
                        "title": "Fresh Title",
                        "video_size": 100,
                        "audio_size": 25,
                    }
                )
                self.worker.retire_flag = True
                return DownloadResult(False, "expected test failure")

            self._run_single_task(
                task_id,
                "https://www.youtube.com/watch?v=fallback-title",
                {"format": "mp3", "normalize_audio": True},
                {"title": "Saved Title"},
                fake_download,
            )

    def test_worker_prefers_reported_final_path_over_same_title_progress_file(self):
        task_id = 80
        completed_events = []
        self.worker.download_finished.connect(
            lambda success, message, emitted_task_id, path: completed_events.append(
                (success, message, emitted_task_id, path)
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "Same Title.mp4"
            reported_path = Path(tmpdir) / "Same Title.webm"
            progress_path.write_text("", encoding="utf-8")
            reported_path.write_text("", encoding="utf-8")

            def fake_download(
                _url,
                _settings,
                progress_hook,
                is_resume=False,
                stop_check=None,
                metadata_hook=None,
                output_path_fallback=None,
            ):
                self.assertFalse(is_resume)
                self.assertTrue(callable(stop_check))
                self.assertTrue(callable(metadata_hook))
                self.assertIsNone(output_path_fallback)
                progress_hook(
                    {
                        "status": "finished",
                        "filename": str(progress_path),
                    }
                )
                self.worker.retire_flag = True
                return DownloadResult(
                    True,
                    "Download complete",
                    str(reported_path),
                )

            self._run_single_task(
                task_id,
                "https://www.youtube.com/watch?v=exact-path",
                {"format": "webm"},
                {"title": "Same Title"},
                fake_download,
            )

        self.assertEqual(
            completed_events,
            [(True, "Download complete", task_id, str(reported_path))],
        )

    def test_worker_does_not_infer_progress_path_when_final_path_was_not_reported(self):
        task_id = 90
        completed_events = []
        self.worker.download_finished.connect(
            lambda success, message, emitted_task_id, path: completed_events.append(
                (success, message, emitted_task_id, path)
            )
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "Fallback Title.mp4"
            progress_path.write_text("", encoding="utf-8")

            def fake_download(
                _url,
                _settings,
                progress_hook,
                is_resume=False,
                stop_check=None,
                metadata_hook=None,
                output_path_fallback=None,
            ):
                progress_hook(
                    {
                        "status": "finished",
                        "filename": str(progress_path),
                    }
                )
                self.worker.retire_flag = True
                return DownloadResult(True, "Download complete")

            self._run_single_task(
                task_id,
                "https://www.youtube.com/watch?v=fallback-path",
                {"format": "mp4"},
                {"title": "Fallback Title"},
                fake_download,
            )

        self.assertEqual(
            completed_events,
            [(True, "Download complete", task_id, "")],
        )

    def test_worker_emits_retained_exact_path_for_failed_finalization(self):
        task_id = 95
        completed_events = []
        self.worker.download_finished.connect(
            lambda success, message, emitted_task_id, path: completed_events.append(
                (success, message, emitted_task_id, path)
            )
        )

        def fake_download(
            _url,
            _settings,
            _progress_hook,
            is_resume=False,
            stop_check=None,
            metadata_hook=None,
        ):
            self.worker.retire_flag = True
            return DownloadResult(
                False,
                "Audio quality finalization failed",
                "C:/Downloads/exact-source.mp4",
            )

        self._run_single_task(
            task_id,
            "https://example.invalid/failed-finalization",
            {"format": "mp4", "audio_quality": "128k"},
            {"title": "Exact source"},
            fake_download,
        )

        self.assertEqual(
            completed_events,
            [
                (
                    False,
                    "Audio quality finalization failed",
                    task_id,
                    "C:/Downloads/exact-source.mp4",
                )
            ],
        )
