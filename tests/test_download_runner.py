import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import MSG_DOWNLOAD_COMPLETE, MSG_PAUSED_BY_USER
from core.download import runner as download_runner


class FakeDownloadWrapper:
    captured = {}
    result = (True, "ok")
    output_path = "C:/Downloads/source.mp4"

    def __init__(self, ytdlp_path, ffmpeg_path=None):
        self.captured["ytdlp_path"] = ytdlp_path
        self.captured["ffmpeg_path"] = ffmpeg_path
        self.final_output_path = self.output_path

    def download(self, url, options, progress_hook, is_resume=False, stop_check=None):
        self.captured["url"] = url
        self.captured["options"] = options
        self.captured["is_resume"] = is_resume
        self.captured["stop_check"] = stop_check
        return self.result


class DownloadRunnerTests(unittest.TestCase):
    def setUp(self):
        FakeDownloadWrapper.captured = {}
        FakeDownloadWrapper.result = (True, "ok")
        FakeDownloadWrapper.output_path = "C:/Downloads/source.mp4"

    def test_download_video_strips_playlist_query_and_returns_complete_message(self):
        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={"built": True}) as build_options, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            success, message = download_runner.download_video(
                "https://www.youtube.com/watch?v=abc123&list=playlist456",
                {"format": "mp4"},
                lambda *_: None,
            )

        self.assertTrue(success)
        self.assertEqual(message, MSG_DOWNLOAD_COMPLETE)
        self.assertEqual(FakeDownloadWrapper.captured["url"], "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(FakeDownloadWrapper.captured["options"], {"built": True})
        build_options.assert_called_once()
        self.assertEqual(
            build_options.call_args.kwargs["url"],
            "https://www.youtube.com/watch?v=abc123",
        )

    def test_download_video_preserves_pause_message(self):
        FakeDownloadWrapper.result = (False, MSG_PAUSED_BY_USER)
        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            success, message = download_runner.download_video(
                "https://example.invalid/video",
                {},
                lambda *_: None,
            )

        self.assertFalse(success)
        self.assertEqual(message, MSG_PAUSED_BY_USER)

    def test_download_video_normalizes_completed_file_and_reports_new_path(self):
        events = []
        normalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/source.mp3",
            error="",
            paused=False,
        )
        settings = {"format": "mp3", "normalize_audio": True}

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "normalize_media_file", return_value=normalized) as normalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            success, message = download_runner.download_video(
                "https://example.invalid/audio",
                settings,
                events.append,
            )

        self.assertTrue(success)
        self.assertEqual(message, MSG_DOWNLOAD_COMPLETE)
        normalize.assert_called_once_with(
            "C:/Downloads/source.mp4",
            settings,
            "ffmpeg.exe",
            None,
        )
        self.assertEqual(events[-1]["filename"], "C:/Downloads/source.mp3")


if __name__ == "__main__":
    unittest.main()
