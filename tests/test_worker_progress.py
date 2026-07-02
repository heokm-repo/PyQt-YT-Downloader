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

from constants import BYTES_PER_MB, STATUS_FINISHED, STATUS_POSTPROCESSING
from core.worker_progress import (
    apply_downloading_progress,
    apply_postprocessing_progress,
    clean_progress_filename,
    format_speed,
)
from locales.strings import STR


class WorkerProgressTests(unittest.TestCase):
    def test_clean_progress_filename_removes_temp_suffixes(self):
        self.assertEqual(clean_progress_filename(r"C:\Downloads\video.mp4.part"), "video.mp4")
        self.assertEqual(clean_progress_filename("audio.webm.ytdl"), "audio.webm")

    def test_format_speed_uses_kb_or_mb(self):
        self.assertEqual(format_speed(1024), "1.0 KB/s")
        self.assertEqual(format_speed(2 * BYTES_PER_MB), "2.0 MB/s")

    def test_apply_downloading_progress_combines_audio_after_video(self):
        progress_info = {
            "video": {"downloaded": 100, "total": 100, "filename": "video.mp4"},
            "audio": {"downloaded": 0, "total": 50, "filename": "audio.webm"},
            "audio_size_est": 50,
        }
        payload = {
            "filename": "audio.webm",
            "downloaded_bytes": 25,
            "total_bytes": 50,
            "speed": 1024,
        }

        apply_downloading_progress(payload, progress_info)

        self.assertEqual(payload["downloaded_bytes"], 125)
        self.assertEqual(payload["total_bytes"], 150)
        self.assertEqual(payload["_percent_str"], "83.3%")
        self.assertEqual(payload["_speed_str"], "1.0 KB/s")

    def test_apply_downloading_progress_assigns_first_seen_file_to_video(self):
        progress_info = {
            "video": {"downloaded": 0, "total": 80, "filename": None},
            "audio": {"downloaded": 0, "total": 20, "filename": None},
            "audio_size_est": 20,
        }
        payload = {"filename": "video.mp4.part", "downloaded_bytes": 120, "total_bytes": 80}

        apply_downloading_progress(payload, progress_info)

        self.assertEqual(progress_info["video"]["filename"], "video.mp4")
        self.assertEqual(payload["_percent_str"], "100.0%")

    def test_apply_postprocessing_progress_marks_processing(self):
        progress_info = {"audio": {"total": 0}, "total_size_est": 150}
        payload = {}

        should_emit = apply_postprocessing_progress(payload, STATUS_POSTPROCESSING, progress_info)

        self.assertTrue(should_emit)
        self.assertEqual(payload["_percent_str"], STR.WORKER_MSG_PROCESSING)
        self.assertEqual(payload["_speed_str"], STR.WORKER_MSG_CONVERTING)
        self.assertEqual(payload["downloaded_bytes"], 150)
        self.assertEqual(payload["total_bytes"], 150)

    def test_apply_postprocessing_progress_waits_for_audio_completion(self):
        progress_info = {
            "audio": {"total": 50, "filename": "audio.webm"},
            "total_size_est": 150,
        }
        payload = {"filename": "video.mp4"}

        should_emit = apply_postprocessing_progress(payload, STATUS_FINISHED, progress_info)

        self.assertFalse(should_emit)
        self.assertNotIn("_percent_str", payload)

    def test_apply_postprocessing_progress_marks_finished_for_audio_file(self):
        progress_info = {
            "audio": {"total": 50, "filename": "audio.webm"},
            "total_size_est": 150,
        }
        payload = {"filename": "audio.webm.ytdl"}

        should_emit = apply_postprocessing_progress(payload, STATUS_FINISHED, progress_info)

        self.assertTrue(should_emit)
        self.assertEqual(payload["_percent_str"], "100%")
        self.assertEqual(payload["_speed_str"], STR.WORKER_MSG_COMPLETED)
        self.assertEqual(payload["total_bytes_estimate"], 150)


if __name__ == "__main__":
    unittest.main()
