import os
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.options import (
    _build_all_options,
    _build_format_options,
)
from core.download.quality_policy import (
    requires_video_quality_finalization,
    video_audio_finalization_bitrate,
)
from core.ytdlp.wrapper import YtDlpWrapper
from constants import AUDIO_QUALITY_OPTIONS


class WebmFormatOptionsTests(unittest.TestCase):
    def test_compatibility_mode_coerces_unsupported_format_to_mp4(self):
        opts = _build_format_options({
            "format": "webm",
            "video_quality": "best",
            "universal_compatibility": True,
        })

        self.assertEqual(
            opts["format"],
            "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        )
        self.assertEqual(opts["merge_output_format"], "mp4")
        self.assertEqual(opts["remux_video"], "mp4")

    def test_webm_best_should_not_require_webm_only_streams(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best"})

        self.assertEqual(
            opts["format"],
            "bestvideo+bestaudio[ext=webm]/bestvideo+bestaudio/best",
        )
        self.assertNotIn("merge_output_format", opts)
        self.assertNotIn("recode_video", opts)

    def test_webm_worst_video_keeps_default_best_audio(self):
        opts = _build_format_options({"format": "webm", "video_quality": "worst"})

        self.assertEqual(
            opts["format"],
            "worstvideo+bestaudio[ext=webm]/worstvideo+bestaudio/worst",
        )
        self.assertNotIn("merge_output_format", opts)
        self.assertNotIn("recode_video", opts)

    def test_webm_quality_caps_the_short_edge_without_webm_only_streams(self):
        opts = _build_format_options({"format": "webm", "video_quality": "720p"})

        self.assertEqual(
            opts["format"],
            "bestvideo+bestaudio[ext=webm]/bestvideo+bestaudio/best",
        )
        self.assertEqual(opts["format_sort"], "res:720")
        self.assertNotIn("merge_output_format", opts)
        self.assertNotIn("recode_video", opts)

    def test_webm_worst_audio_is_applied_to_video_downloads(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best", "audio_quality": "worst"})

        self.assertEqual(
            opts["format"],
            "bestvideo+worstaudio[ext=webm]/bestvideo+worstaudio/best",
        )
        self.assertNotIn("merge_output_format", opts)
        self.assertNotIn("recode_video", opts)
        self.assertNotIn("postprocessor_args", opts)

    def test_webm_numeric_audio_quality_controls_recode_bitrate(self):
        opts = _build_format_options({"format": "webm", "video_quality": "best", "audio_quality": "256k"})

        self.assertEqual(
            opts["format"],
            "bestvideo+bestaudio[ext=webm]/bestvideo+bestaudio/best",
        )
        self.assertNotIn("recode_video", opts)
        self.assertNotIn("postprocessor_args", opts)

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
    def test_video_containers_select_compatible_worst_audio_source(self):
        expected = {
            "mp4": "bestvideo+worstaudio[ext=m4a]/bestvideo+worstaudio/best",
            "mkv": "bestvideo+worstaudio/best",
            "webm": "bestvideo+worstaudio[ext=webm]/bestvideo+worstaudio/best",
        }
        for fmt, selector in expected.items():
            with self.subTest(fmt=fmt):
                opts = _build_format_options({
                    "format": fmt,
                    "video_quality": "best",
                    "audio_quality": "worst",
                })

                self.assertEqual(opts["format"], selector)

    def test_video_containers_select_compatible_best_audio_for_numeric_quality(self):
        expected = {
            "mp4": "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "mkv": "bestvideo+bestaudio/best",
            "webm": "bestvideo+bestaudio[ext=webm]/bestvideo+bestaudio/best",
        }
        for fmt, selector in expected.items():
            with self.subTest(fmt=fmt):
                opts = _build_format_options({
                    "format": fmt,
                    "video_quality": "best",
                    "audio_quality": "128k",
                })

                self.assertEqual(opts["format"], selector)

    def test_video_short_edge_and_numeric_audio_quality_do_not_reduce_source_audio(self):
        opts = _build_format_options({
            "format": "mp4",
            "video_quality": "720p",
            "audio_quality": "128k",
        })

        self.assertEqual(
            opts["format"],
            "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        )
        self.assertEqual(opts["format_sort"], "res:720")

    def test_new_high_resolution_options_cap_the_short_edge(self):
        for quality, expected_sort in (
            ("2160p", "res:2160"),
            ("1440p", "res:1440"),
        ):
            with self.subTest(quality=quality):
                opts = _build_format_options({
                    "format": "mp4",
                    "video_quality": quality,
                })

                self.assertEqual(
                    opts["format"],
                    "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                )
                self.assertEqual(opts["format_sort"], expected_sort)

    def test_cli_maps_short_edge_format_sort_when_present(self):
        cmd = YtDlpWrapper("yt-dlp.exe")._build_command(
            "https://example.invalid/video",
            {
                "format": "bestvideo+bestaudio/best",
                "format_sort": "res:1080",
            },
            False,
        )

        self.assertIn("--format-sort", cmd)
        self.assertEqual(cmd[cmd.index("--format-sort") + 1], "res:1080")

    def test_mp4_and_mkv_numeric_quality_use_app_audio_finalization(self):
        for fmt in ("mp4", "mkv"):
            with self.subTest(fmt=fmt):
                self.assertEqual(
                    video_audio_finalization_bitrate(fmt, "128k", False),
                    "128k",
                )
                self.assertEqual(
                    video_audio_finalization_bitrate(fmt, "worst", False),
                    "48k",
                )
                self.assertIsNone(
                    video_audio_finalization_bitrate(fmt, "best", False)
                )
                self.assertIsNone(
                    video_audio_finalization_bitrate(fmt, "128k", True)
                )

        self.assertTrue(
            requires_video_quality_finalization("webm", "best", False)
        )
        self.assertIsNone(
            video_audio_finalization_bitrate("webm", "best", False)
        )
        self.assertEqual(
            video_audio_finalization_bitrate("webm", "128k", False),
            "128k",
        )

    def test_video_container_outputs_still_use_expected_output_mode(self):
        mp4_opts = _build_format_options({"format": "mp4", "audio_quality": "worst"})
        mkv_opts = _build_format_options({"format": "mkv", "audio_quality": "worst"})
        webm_opts = _build_format_options({"format": "webm", "audio_quality": "worst"})

        self.assertEqual(mp4_opts["merge_output_format"], "mp4")
        self.assertEqual(mkv_opts["merge_output_format"], "mkv")
        self.assertEqual(mp4_opts["remux_video"], "mp4")
        self.assertEqual(mkv_opts["remux_video"], "mkv")
        self.assertNotIn("postprocessor_args", mp4_opts)
        self.assertNotIn("postprocessor_args", mkv_opts)
        self.assertNotIn("merge_output_format", webm_opts)
        self.assertNotIn("remux_video", webm_opts)
        self.assertNotIn("recode_video", webm_opts)
        self.assertNotIn("postprocessor_args", webm_opts)


class AudioOnlyFormatOptionsTests(unittest.TestCase):
    def test_audio_quality_options_include_96k(self):
        self.assertEqual(
            AUDIO_QUALITY_OPTIONS,
            ["best", "320k", "256k", "192k", "128k", "96k", "worst"],
        )

    def test_m4a_prefers_compatible_aac_sources(self):
        best = _build_format_options({"format": "m4a", "audio_quality": "192k"})
        worst = _build_format_options({"format": "m4a", "audio_quality": "worst"})

        self.assertEqual(
            best["format"],
            (
                "bestaudio[ext=m4a]/"
                "bestaudio[acodec^=mp4a]/"
                "bestaudio[acodec=aac]/"
                "best[acodec^=mp4a]/"
                "best[acodec=aac]/"
                "bestaudio/best"
            ),
        )
        self.assertEqual(
            worst["format"],
            (
                "worstaudio[ext=m4a]/"
                "worstaudio[acodec^=mp4a]/"
                "worstaudio[acodec=aac]/"
                "worst[acodec^=mp4a]/"
                "worst[acodec=aac]/"
                "worstaudio/worst"
            ),
        )

    def test_mp3_best_defers_single_conversion_to_app_finalizer(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "best"})

        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertNotIn("extract_audio", opts)
        self.assertNotIn("audio_quality", opts)

    def test_mp3_worst_still_downloads_best_source_once(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "worst"})

        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertNotIn("extract_audio", opts)

    def test_mp3_numeric_quality_is_not_forwarded_to_ytdlp(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "320k"})

        self.assertEqual(opts["format"], "bestaudio/best")
        self.assertNotIn("audio_quality", opts)

    def test_wav_omits_lossy_encoder_quality(self):
        for quality in ("best", "320k", "worst"):
            with self.subTest(quality=quality):
                opts = _build_format_options({"format": "wav", "audio_quality": quality})

                self.assertEqual(opts["format"], "bestaudio/best")
                self.assertNotIn("extract_audio", opts)
                self.assertNotIn("audio_quality", opts)

    def test_mp3_does_not_add_ytdlp_postprocessor_args(self):
        opts = _build_format_options({"format": "mp3", "audio_quality": "worst"})

        self.assertNotIn("postprocessor_args", opts)

    def test_mp3_normalization_defers_conversion_to_app_ffmpeg_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            opts = _build_all_options(
                {"format": "mp3", "audio_quality": "worst", "normalize_audio": True},
                tmpdir,
                "ffmpeg.exe",
                is_playlist=False,
            )

        self.assertEqual(opts["format"], "bestaudio/best")
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
        self.assertEqual(mp4_opts["remux_video"], "mp4")
        self.assertNotIn("postprocessor_args", mp4_opts)
        self.assertNotIn("recode_video", webm_opts)
        self.assertNotIn("remux_video", webm_opts)
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
