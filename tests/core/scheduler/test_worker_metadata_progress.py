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
            "core.workers.download_handler.fetch_metadata",
            side_effect=AssertionError("metadata preflight must not run"),
        ) as fetch_metadata, patch(
            "core.workers.download_handler.download_video_with_result",
            side_effect=fake_download,
        ):
            self.worker.run()
        fetch_metadata.assert_not_called()

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

    def test_worker_uses_inline_metadata_without_preflight_and_updates_estimates(self):
        task_id = 50
        metadata_events = []
        progress_events = []
        started_events = []
        tracking_snapshots = []
        event_order = []

        def record_metadata(emitted_task_id, metadata):
            event_order.append("metadata")
            metadata_events.append((emitted_task_id, metadata.copy()))

        def record_progress(data, emitted_task_id):
            event_order.append("progress")
            progress_events.append((emitted_task_id, data.copy()))

        def record_started(emitted_task_id):
            event_order.append("started")
            started_events.append(emitted_task_id)

        self.worker.metadata_fetched.connect(record_metadata)
        self.worker.progress_updated.connect(record_progress)
        self.worker.task_started.connect(record_started)

        def fake_download(
            url,
            settings,
            progress_hook,
            is_resume=False,
            stop_check=None,
            metadata_hook=None,
            output_path_fallback=None,
        ):
            self.assertEqual(url, "https://www.youtube.com/watch?v=inline")
            self.assertEqual(settings["format"], "mp4")
            self.assertEqual(
                settings["_temp_identity"],
                {
                    "id": None,
                    "extractor": "unknown",
                    "workspace_id": None,
                    "legacy_workspace": False,
                    "legacy_identity": None,
                },
            )
            self.assertFalse(is_resume)
            self.assertTrue(callable(stop_check))
            self.assertTrue(callable(metadata_hook))
            self.assertIsNone(output_path_fallback)

            metadata_hook(
                {
                    "id": "inline",
                    "title": "Inline metadata",
                    "extractor": "youtube",
                    "video_size": 100,
                    "audio_size": 25,
                    "audio_bitrate": 136_515,
                }
            )
            self.assertEqual(settings["_selected_audio_bitrate"], 136_515)
            progress_state = self.worker.download_progress[task_id]
            tracking_snapshots.append(
                {
                    "video_total": progress_state["video"]["total"],
                    "audio_total": progress_state["audio"]["total"],
                    "total_size_est": progress_state["total_size_est"],
                }
            )
            progress_hook(
                {
                    "status": "downloading",
                    "filename": "video.mp4",
                    "downloaded_bytes": 10,
                    "total_bytes": 100,
                    "speed": 1024,
                }
            )
            self.worker.retire_flag = True
            return DownloadResult(False, "expected test failure")

        self._run_single_task(
            task_id,
            "https://www.youtube.com/watch?v=inline",
            {"format": "mp4"},
            {},
            fake_download,
        )

        self.assertEqual(
            metadata_events,
            [
                (
                    task_id,
                    {
                        "id": "inline",
                        "title": "Inline metadata",
                        "extractor": "youtube",
                        "video_size": 100,
                        "audio_size": 25,
                        "audio_bitrate": 136_515,
                    },
                )
            ],
        )
        self.assertEqual(
            tracking_snapshots,
            [{"video_total": 100, "audio_total": 25, "total_size_est": 125}],
        )
        self.assertEqual(len(progress_events), 1)
        self.assertEqual(progress_events[0][0], task_id)
        self.assertEqual(progress_events[0][1]["total_bytes"], 125)
        self.assertEqual(started_events, [task_id])
        self.assertEqual(event_order, ["metadata", "started", "progress"])

    def test_worker_ignores_repeated_inline_metadata_without_resetting_progress(self):
        task_id = 60
        metadata_events = []
        progress_state_snapshots = []
        self.worker.metadata_fetched.connect(
            lambda emitted_task_id, metadata: metadata_events.append(
                (emitted_task_id, metadata.copy())
            )
        )

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
            metadata_hook(
                {
                    "id": "repeat",
                    "title": "First metadata",
                    "extractor": "youtube",
                    "video_size": 100,
                    "audio_size": 25,
                }
            )
            progress_hook(
                {
                    "status": "downloading",
                    "filename": "video.mp4",
                    "downloaded_bytes": 40,
                    "total_bytes": 100,
                    "speed": 1024,
                }
            )
            state = self.worker.download_progress[task_id]
            progress_state_snapshots.append(
                (
                    state["video"]["downloaded"],
                    state["video"]["total"],
                    state["total_size_est"],
                )
            )

            metadata_hook(
                {
                    "id": "repeat",
                    "title": "Repeated metadata",
                    "extractor": "youtube",
                    "video_size": 999,
                    "audio_size": 999,
                }
            )
            state = self.worker.download_progress[task_id]
            progress_state_snapshots.append(
                (
                    state["video"]["downloaded"],
                    state["video"]["total"],
                    state["total_size_est"],
                )
            )
            self.worker.retire_flag = True
            return DownloadResult(False, "expected test failure")

        self._run_single_task(
            task_id,
            "https://www.youtube.com/watch?v=repeat",
            {"format": "mp4"},
            {},
            fake_download,
        )

        self.assertEqual(len(metadata_events), 1)
        self.assertEqual(metadata_events[0][0], task_id)
        self.assertEqual(metadata_events[0][1]["title"], "First metadata")
        self.assertEqual(
            progress_state_snapshots,
            [(40, 100, 125), (40, 100, 125)],
        )

    def test_worker_merges_fresh_metadata_over_saved_metadata(self):
        task_id = 70
        metadata_events = []
        progress_estimates = []
        self.worker.metadata_fetched.connect(
            lambda emitted_task_id, metadata: metadata_events.append(
                (emitted_task_id, metadata.copy())
            )
        )

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
                    "id": "merge",
                    "title": "Fresh title",
                    "uploader": "Fresh uploader",
                    "extractor": "youtube",
                    "video_size": 100,
                    "audio_size": 25,
                }
            )
            state = self.worker.download_progress[task_id]
            progress_estimates.append(
                (
                    state["video"]["total"],
                    state["audio"]["total"],
                    state["total_size_est"],
                )
            )
            self.worker.retire_flag = True
            return DownloadResult(False, "expected test failure")

        self._run_single_task(
            task_id,
            "https://www.youtube.com/watch?v=merge",
            {"format": "mp4"},
            {
                "title": "Saved title",
                "thumbnail": "https://example.invalid/saved-thumb.jpg",
                "file_size": 4096,
                "saved_only": "keep",
                "video_size": 1,
                "audio_size": 2,
            },
            fake_download,
        )

        self.assertEqual(
            metadata_events,
            [
                (
                    task_id,
                    {
                        "title": "Fresh title",
                        "thumbnail": "https://example.invalid/saved-thumb.jpg",
                        "file_size": 4096,
                        "saved_only": "keep",
                        "video_size": 100,
                        "audio_size": 25,
                        "id": "merge",
                        "uploader": "Fresh uploader",
                        "extractor": "youtube",
                    },
                )
            ],
        )
        self.assertEqual(progress_estimates, [(100, 25, 125)])
