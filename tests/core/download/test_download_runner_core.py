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
        finalizer_patcher = patch.object(
            download_runner,
            "finalize_and_commit_download",
            side_effect=lambda path, _workspace, _folder, _settings, _ffmpeg, _stop: SimpleNamespace(
                success=True,
                output_path=path,
                error="",
                paused=False,
            ),
        )
        finalizer_patcher.start()
        self.addCleanup(finalizer_patcher.stop)
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

    def test_download_video_strips_playlist_query_and_returns_complete_message(self):
        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={"built": True}) as build_options, \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://www.youtube.com/watch?v=abc123&list=playlist456",
                {"format": "mp4"},
                lambda *_: None,
            )
            success, message = result.success, result.message

        self.assertTrue(success)
        self.assertEqual(message, MSG_DOWNLOAD_COMPLETE)
        self.assertEqual(FakeDownloadWrapper.captured["url"], "https://www.youtube.com/watch?v=abc123")
        self.assertEqual(FakeDownloadWrapper.captured["options"], {"built": True})
        build_options.assert_called_once()
        self.assertEqual(
            build_options.call_args.kwargs["url"],
            "https://www.youtube.com/watch?v=abc123",
        )
        self.assertTrue(callable(FakeDownloadWrapper.captured["metadata_hook"]))
    def test_download_video_result_includes_wrapper_final_output_path(self):
        FakeDownloadWrapper.output_path = "C:/Downloads/exact-source.mkv"
        finalized = SimpleNamespace(
            success=True,
            output_path="C:/Downloads/exact-output.webm",
            error="",
            paused=False,
        )

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
                {"format": "webm"},
                lambda *_: None,
            )
            success, message = result.success, result.message

        self.assertTrue(result.success)
        self.assertEqual(result.message, MSG_DOWNLOAD_COMPLETE)
        self.assertEqual(result.final_path, "C:/Downloads/exact-output.webm")
        finalize.assert_called_once_with(
            "C:/Downloads/exact-source.mkv",
            "",
            "C:/Downloads",
            {"format": "webm"},
            "ffmpeg.exe",
            None,
        )

    def test_download_video_fails_when_final_path_marker_is_missing(self):
        FakeDownloadWrapper.output_path = None

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://example.invalid/video",
                {"format": "webm"},
                lambda *_: None,
            )
            success, message = result.success, result.message

        self.assertFalse(result.success)
        self.assertEqual(
            result.message,
            download_runner.OUTPUT_PATH_VERIFICATION_ERROR,
        )
        self.assertEqual(result.final_path, "")

    def test_download_video_maps_inline_raw_info_before_calling_app_metadata_hook(self):
        metadata_events = []
        FakeDownloadWrapper.raw_info = {
            "id": "abc123",
            "title": "Inline metadata",
            "channel": "Channel",
            "extractor": "YouTube",
            "thumbnail": "https://example.invalid/thumb.jpg",
            "requested_formats": [
                {
                    "vcodec": "avc1",
                    "acodec": "none",
                    "filesize": 100,
                },
                {
                    "vcodec": "none",
                    "acodec": "opus",
                    "filesize_approx": 25,
                },
            ],
        }

        with patch.object(download_runner, "get_ytdlp_path", return_value="yt-dlp.exe"), \
             patch.object(download_runner, "get_ffmpeg_path", return_value="ffmpeg.exe"), \
             patch.object(download_runner, "get_download_folder", return_value="C:/Downloads"), \
             patch.object(download_runner, "_build_all_options", return_value={}), \
             patch.object(download_runner, "YtDlpWrapper", FakeDownloadWrapper):
            result = download_runner.download_video_with_result(
                "https://www.youtube.com/watch?v=abc123&list=playlist456",
                {"format": "mp4"},
                lambda *_: None,
                metadata_hook=metadata_events.append,
            )
            success, message = result.success, result.message

        self.assertTrue(success)
        self.assertEqual(message, MSG_DOWNLOAD_COMPLETE)
        self.assertEqual(len(metadata_events), 1)
        self.assertEqual(
            metadata_events[0],
            {
                "title": "Inline metadata",
                "uploader": "Channel",
                "duration": 0,
                "thumbnail": "https://example.invalid/thumb.jpg",
                "id": "abc123",
                "extractor": "youtube",
                "webpage_url": "https://www.youtube.com/watch?v=abc123",
                "video_size": 100,
                "audio_size": 25,
                "download_streams": [
                    {"id": "0", "kind": "video", "size": 100},
                    {"id": "1", "kind": "audio", "size": 25},
                ],
            },
        )
        self.assertTrue(callable(FakeDownloadWrapper.captured["metadata_hook"]))
