import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
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
    raw_info = None
    progress_events = []

    def __init__(self, ytdlp_path, ffmpeg_path=None):
        self.captured["ytdlp_path"] = ytdlp_path
        self.captured["ffmpeg_path"] = ffmpeg_path
        self.final_output_path = self.output_path

    def download(
        self,
        url,
        options,
        progress_hook,
        is_resume=False,
        stop_check=None,
        metadata_hook=None,
    ):
        self.captured["url"] = url
        self.captured["options"] = options
        self.captured["is_resume"] = is_resume
        self.captured["stop_check"] = stop_check
        self.captured["metadata_hook"] = metadata_hook
        if metadata_hook is not None and self.raw_info is not None:
            metadata_hook(self.raw_info)
        for event in self.progress_events:
            progress_hook(event.copy())
        return self.result


class DownloadRunnerTests(unittest.TestCase):
    def setUp(self):
        FakeDownloadWrapper.captured = {}
        FakeDownloadWrapper.result = (True, "ok")
        FakeDownloadWrapper.output_path = "C:/Downloads/source.mp4"
        FakeDownloadWrapper.raw_info = None
        FakeDownloadWrapper.progress_events = []
        output_path_patcher = patch.object(
            download_runner,
            "verified_download_output_path",
            side_effect=lambda path, _folder: str(path or ""),
        )
        output_path_patcher.start()
        self.addCleanup(output_path_patcher.stop)
        workspace_path_patcher = patch.object(
            download_runner,
            "verified_workspace_output_path",
            side_effect=lambda path, _workspace: str(path or ""),
        )
        workspace_path_patcher.start()
        self.addCleanup(workspace_path_patcher.stop)

    def test_normalization_rejects_progress_path_when_final_marker_is_missing(self):
        events = []
        FakeDownloadWrapper.output_path = None
        FakeDownloadWrapper.progress_events = [
            {
                "status": "finished",
                "filename": "C:/Downloads/progress-source.webm",
            }
        ]
        normalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/progress-source.mp3",
            error="",
            paused=False,
        )
        settings = {"format": "mp3", "normalize_audio": True}

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "finalize_and_commit_download", return_value=normalized) as normalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/audio",
                settings,
                events.append,
            )

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            download_runner.OUTPUT_PATH_VERIFICATION_ERROR,
        )
        self.assertEqual(result.final_path, "")
        normalize.assert_not_called()

    def test_normalization_does_not_use_title_fallback_when_marker_is_missing(self):
        events = []
        FakeDownloadWrapper.output_path = None
        normalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/found-source.mp3",
            error="",
            paused=False,
        )
        settings = {"format": "mp3", "normalize_audio": True}

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "finalize_and_commit_download", return_value=normalized) as normalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/audio",
                settings,
                events.append,
            )

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            download_runner.OUTPUT_PATH_VERIFICATION_ERROR,
        )
        self.assertEqual(result.final_path, "")
        normalize.assert_not_called()

    def test_normalization_failure_does_not_report_source_as_final_path(self):
        normalized = SimpleNamespace(
            success=False,
            output_path="C:/Downloads/source.mp4",
            error="normalization failed",
            paused=False,
        )
        settings = {"format": "mp3", "normalize_audio": True}

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "write_ready_source"), \
             patch.object(download_runner, "finalize_and_commit_download", return_value=normalized), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/audio",
                settings,
                lambda *_: None,
            )

        self.assertFalse(result.success)
        self.assertIn("normalization failed", result.message)
        self.assertEqual(result.final_path, "C:/Downloads/source.mp4")


if __name__ == "__main__":
    unittest.main()
