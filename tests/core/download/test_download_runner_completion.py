import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import MSG_DOWNLOAD_COMPLETE, MSG_PAUSED_BY_USER
from core.download import runner as download_runner
from core.download.workspace_state import ReadySource


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
        ready_patcher = patch.object(
            download_runner,
            "write_ready_source",
            return_value=SimpleNamespace(),
        )
        ready_patcher.start()
        self.addCleanup(ready_patcher.stop)
        cleanup_patcher = patch.object(
            download_runner,
            "remove_task_workspace",
            return_value=True,
        )
        cleanup_patcher.start()
        self.addCleanup(cleanup_patcher.stop)

    def test_download_video_preserves_pause_message(self):
        FakeDownloadWrapper.result = (False, MSG_PAUSED_BY_USER)
        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                {},
                lambda *_: None,
            )

        self.assertFalse(result.success)
        self.assertEqual(result.message, MSG_PAUSED_BY_USER)
        self.assertEqual(result.final_path, "")

    def test_ready_source_resume_skips_ytdlp_and_runs_finalization(self):
        wrapper = MagicMock()
        finalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/title.mp4",
            error="",
            paused=False,
        )
        settings = {"format": "mp4"}
        verification_calls = {"count": 0}

        def verify_after_finalization(path, _folder):
            verification_calls["count"] += 1
            return path if verification_calls["count"] >= 3 else ""

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(
                 download_runner,
                 "_build_all_options",
                 return_value={"temp_path": "C:/Downloads/.ytdl_temp/0123456789abcdef"},
             ), \
             patch.object(
                 download_runner,
                 "read_ready_source",
                 return_value=ReadySource(
                     "C:/Downloads/.ytdl_temp/0123456789abcdef/title.mp4",
                     "title.mp4",
                     129_500,
                 ),
             ), \
             patch.object(
                 download_runner,
                 "verified_download_output_path",
                 side_effect=verify_after_finalization,
             ), \
             patch.object(
                 download_runner,
                 "finalize_and_commit_download",
                 return_value=finalized,
             ) as finalize, \
             patch.object(download_runner, "YtDlpWrapper", return_value=wrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                settings,
                lambda *_: None,
                is_resume=True,
            )

        self.assertTrue(result.success)
        wrapper.download.assert_not_called()
        finalize.assert_called_once()
        self.assertEqual(settings["_selected_audio_bitrate"], 129_500)

    def test_download_video_normalizes_completed_file_and_reports_new_path(self):
        events = []
        FakeDownloadWrapper.raw_info = {
            "id": "source",
            "title": "Source",
            "acodec": "opus",
            "asr": 48000,
        }
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
             patch.object(download_runner, "finalize_and_commit_download", return_value=normalized) as normalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/audio",
                settings,
                events.append,
            )

        self.assertTrue(result.success)
        self.assertEqual(result.message, MSG_DOWNLOAD_COMPLETE)
        self.assertEqual(result.final_path, "C:/Downloads/source.mp3")
        normalize.assert_called_once_with(
            "C:/Downloads/source.mp4",
            "",
            "C:/Downloads",
            settings,
            "ffmpeg.exe",
            None,
        )
        self.assertEqual(events[-1]["filename"], "C:/Downloads/source.mp3")

    def test_numeric_video_audio_quality_finalizes_exact_reported_path(self):
        events = []
        FakeDownloadWrapper.output_path = "C:/Downloads/exact-source.mp4"
        finalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/exact-source.mp4",
            error="",
            paused=False,
        )
        settings = {
            "format": "mp4",
            "audio_quality": "128k",
            "normalize_audio": False,
        }

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(
                 download_runner,
                 "finalize_and_commit_download",
                 return_value=finalized,
             ) as finalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                settings,
                events.append,
            )

        self.assertTrue(result.success)
        self.assertEqual(result.final_path, "C:/Downloads/exact-source.mp4")
        finalize.assert_called_once_with(
            "C:/Downloads/exact-source.mp4",
            "",
            "C:/Downloads",
            settings,
            "ffmpeg.exe",
            None,
        )
        self.assertEqual(events[-1]["status"], "finished")

    def test_compatibility_mode_finalizes_mp4_after_download(self):
        events = []
        compatible = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/source.mp4",
            error="",
            paused=False,
        )
        settings = {
            "format": "mp4",
            "universal_compatibility": True,
        }

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(
                 download_runner,
                 "finalize_and_commit_download",
                 return_value=compatible,
             ) as finalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                settings,
                events.append,
            )

        self.assertTrue(result.success)
        finalize.assert_called_once_with(
            "C:/Downloads/source.mp4",
            "",
            "C:/Downloads",
            settings,
            "ffmpeg.exe",
            None,
        )
        self.assertEqual(events[-1]["status"], "finished")

    def test_compatibility_mode_does_not_finalize_mp3(self):
        settings = {
            "format": "mp3",
            "universal_compatibility": True,
        }

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(
                 download_runner,
                 "finalize_and_commit_download",
                 return_value=SimpleNamespace(
                     success=True,
                     output_path="C:/Downloads/source.mp3",
                     error="",
                     paused=False,
                 ),
             ) as finalize, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/audio",
                settings,
                lambda *_: None,
            )

        self.assertTrue(result.success)
        finalize.assert_called_once()

    def test_audio_quality_finalization_failure_retains_exact_source_path(self):
        FakeDownloadWrapper.output_path = "C:/Downloads/exact-source.mp4"
        failed = SimpleNamespace(
            success=False,
            output_path="C:/Downloads/exact-source.mp4",
            error="encoder failed",
            paused=False,
        )
        settings = {
            "format": "mp4",
            "audio_quality": "128k",
            "normalize_audio": False,
        }

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(
                 download_runner,
                 "finalize_and_commit_download",
                 return_value=failed,
             ), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                settings,
                lambda *_: None,
            )

        self.assertFalse(result.success)
        self.assertIn("encoder failed", result.message)
        self.assertEqual(result.final_path, "C:/Downloads/exact-source.mp4")
