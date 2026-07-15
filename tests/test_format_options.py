import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.options import (
    AUDIO_EXTRACT_FFMPEG_ARGS_KEY,
    _build_all_options,
    _build_format_options,
)
from core.ytdlp.wrapper import YtDlpWrapper


class WebmFormatOptionsTests(unittest.TestCase):
    def test_webm_best_should_not_require_webm_only_streams(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best"})

        self.assertEqual(opts["format"], "bestvideo+bestaudio/best")
        self.assertNotIn("merge_output_format", opts)
        self.assertEqual(opts["recode_video"], "webm")

    def test_webm_worst_video_keeps_default_best_audio(self):
        opts = _build_format_options({"format": "webm", "video_quality": "worst"})

        self.assertEqual(opts["format"], "worstvideo+bestaudio/worst")
        self.assertNotIn("merge_output_format", opts)
        self.assertEqual(opts["recode_video"], "webm")

    def test_webm_height_preserves_height_limit_without_webm_only_streams(self):
        opts = _build_format_options({"format": "webm", "video_quality": "720p"})

        self.assertEqual(opts["format"], "bestvideo[height<=720]+bestaudio/best[height<=720]")
        self.assertNotIn("merge_output_format", opts)
        self.assertEqual(opts["recode_video"], "webm")

    def test_webm_worst_audio_is_applied_to_video_downloads(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best", "audio_quality": "worst"})

        self.assertEqual(opts["format"], "bestvideo+worstaudio/best")
        self.assertNotIn("merge_output_format", opts)
        self.assertEqual(opts["recode_video"], "webm")
        self.assertEqual(opts["postprocessor_args"], {"ffmpeg": ["-b:a", "48k"]})

    def test_webm_numeric_audio_quality_controls_recode_bitrate(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best", "audio_quality": "256k"})

        self.assertEqual(opts["format"], "bestvideo+bestaudio[abr<=256]/bestvideo+bestaudio/best")
        self.assertEqual(opts["recode_video"], "webm")
        self.assertEqual(opts["postprocessor_args"], {"ffmpeg": ["-b:a", "256k"]})

    def test_cli_maps_recode_video_when_present(self):
        cmd = YtDlpWrapper("yt-dlp.exe")._build_command(
            "https://example.invalid/video",
            {
                "format": "worstvideo+worstaudio/worst",
                "recode_video": "webm",
            },
            False,
        )

        self.assertIn("--recode-video", cmd)
        self.assertEqual(cmd[cmd.index("--recode-video") + 1], "webm")


class VideoContainerAudioQualityTests(unittest.TestCase):
    def test_video_containers_apply_worst_audio_quality(self):
        for fmt in ("mp4", "mkv", "webm"):
            with self.subTest(fmt=fmt):
                opts = _build_format_options({
                    "format": fmt,
                    "video_quality": "best",
                    "audio_quality": "worst",
                })

                self.assertEqual(opts["format"], "bestvideo+worstaudio/best")

    def test_video_containers_apply_numeric_audio_quality_limit(self):
        for fmt in ("mp4", "mkv", "webm"):
            with self.subTest(fmt=fmt):
                opts = _build_format_options({
                    "format": fmt,
                    "video_quality": "best",
                    "audio_quality": "128k",
                })

                self.assertEqual(opts["format"], "bestvideo+bestaudio[abr<=128]/bestvideo+bestaudio/best")

    def test_video_height_and_numeric_audio_quality_are_combined(self):
        opts = _build_format_options({
            "format": "mp4",
            "video_quality": "720p",
            "audio_quality": "128k",
        })

        self.assertEqual(
            opts["format"],
            "bestvideo[height<=720]+bestaudio[abr<=128]/bestvideo[height<=720]+bestaudio/best[height<=720]",
        )

    def test_video_container_outputs_still_use_expected_output_mode(self):
        mp4_opts = _build_format_options({"format": "mp4", "audio_quality": "worst"})
        mkv_opts = _build_format_options({"format": "mkv", "audio_quality": "worst"})
        webm_opts = _build_format_options({"format": "webm", "audio_quality": "worst"})

        self.assertEqual(mp4_opts["merge_output_format"], "mp4")
        self.assertEqual(mkv_opts["merge_output_format"], "mkv")
        self.assertNotIn("postprocessor_args", mp4_opts)
        self.assertNotIn("postprocessor_args", mkv_opts)
        self.assertNotIn("merge_output_format", webm_opts)
        self.assertEqual(webm_opts["recode_video"], "webm")
        self.assertEqual(webm_opts["postprocessor_args"], {"ffmpeg": ["-b:a", "48k"]})


class AudioOnlyFormatOptionsTests(unittest.TestCase):
    def test_mp3_best_uses_best_audio_source_and_best_encoder_quality(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "best"})

        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertTrue(opts["extract_audio"])
        self.assertEqual(opts["audio_format"], "mp3")
        self.assertEqual(opts["audio_quality"], "0")

    def test_mp3_worst_uses_worst_audio_source_and_worst_encoder_quality(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "worst"})

        self.assertEqual(opts["format"], "worstaudio/worst")
        self.assertTrue(opts["extract_audio"])
        self.assertEqual(opts["audio_format"], "mp3")
        self.assertEqual(opts["audio_quality"], "10")

    def test_mp3_numeric_quality_is_forwarded_to_ffmpeg(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "320k"})

        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertEqual(opts["audio_quality"], "320k")

    def test_mp3_postprocessor_args_are_scoped_to_extract_audio(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "worst"})

        self.assertEqual(
            opts["postprocessor_args"],
            {AUDIO_EXTRACT_FFMPEG_ARGS_KEY: ["-ac", "2"]},
        )

    def test_mp3_normalization_defers_conversion_to_app_ffmpeg_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = _build_all_options(
                {"format": "mp3", "audio_quality": "worst", "normalize_audio": True},
                tmpdir,
                "ffmpeg.exe",
                is_playlist=False,
                progress_hook=lambda _: None,
            )

        self.assertEqual(opts["format"], "worstaudio/worst")
        self.assertNotIn("extract_audio", opts)
        self.assertNotIn("audio_format", opts)
        self.assertNotIn("postprocessor_args", opts)

    def test_video_normalization_does_not_inject_filter_into_ytdlp_merger(self):
        mp4_opts = _build_format_options({
            "format": "mp4",
            "video_quality": "worst",
            "audio_quality": "worst",
            "normalize_audio": True,
        })
        webm_opts = _build_format_options({
            "format": "webm",
            "video_quality": "worst",
            "audio_quality": "worst",
            "normalize_audio": True,
        })

        self.assertEqual(mp4_opts["merge_output_format"], "mp4")
        self.assertNotIn("postprocessor_args", mp4_opts)
        self.assertNotIn("recode_video", webm_opts)
        self.assertNotIn("postprocessor_args", webm_opts)

    def test_cli_maps_audio_quality_when_present(self):
        cmd = YtDlpWrapper("yt-dlp.exe")._build_command(
            "https://example.invalid/audio",
            {
                "format": "bestaudio/best",
                "extract_audio": True,
                "audio_format": "mp3",
                "audio_quality": "320k",
            },
            False,
        )

        self.assertIn("--audio-quality", cmd)
        self.assertEqual(cmd[cmd.index("--audio-quality") + 1], "320k")


if __name__ == "__main__":
    unittest.main()
