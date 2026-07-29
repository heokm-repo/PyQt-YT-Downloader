import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.ffmpeg_process import FfmpegExecutionResult
from core.download.finalization_command import build_finalization_command
from core.download.finalization_pipeline import finalize_and_commit_download
from core.download.finalization_policy import build_finalization_plan
from core.download.media_probe import MediaProbeResult


class FinalizationPolicyTests(unittest.TestCase):
    def test_m4a_copies_aac_when_source_is_under_requested_quality(self):
        plan = build_finalization_plan(
            {
                "format": "m4a",
                "audio_quality": "192k",
                "_selected_audio_bitrate": 129_500,
            },
            MediaProbeResult(audio_codec="aac", audio_sample_rate=44100),
        )

        self.assertEqual(plan.audio_args, ("-c:a", "copy"))
        self.assertFalse(plan.requires_ffmpeg)

    def test_m4a_encodes_aac_when_source_exceeds_requested_quality(self):
        plan = build_finalization_plan(
            {
                "format": "m4a",
                "audio_quality": "96k",
                "_selected_audio_bitrate": 129_500,
            },
            MediaProbeResult(audio_codec="aac", audio_sample_rate=44100),
        )

        self.assertEqual(plan.audio_args, ("-c:a", "aac", "-b:a", "96k"))
        self.assertTrue(plan.requires_ffmpeg)

    def test_m4a_extracts_combined_aac_without_reencoding(self):
        plan = build_finalization_plan(
            {"format": "m4a", "audio_quality": "best"},
            MediaProbeResult(
                audio_codec="aac",
                video_codec="h264",
            ),
            "combined.mp4",
        )
        command = build_finalization_command(
            "ffmpeg.exe",
            "combined.mp4",
            "output.m4a",
            plan,
        )

        self.assertTrue(plan.requires_ffmpeg)
        self.assertEqual(plan.audio_args, ("-c:a", "copy"))
        self.assertIn("-vn", command)
        self.assertEqual(command[command.index("-map") + 1], "0:a:0?")

    def test_m4a_remuxes_standalone_raw_aac(self):
        plan = build_finalization_plan(
            {"format": "m4a", "audio_quality": "best"},
            MediaProbeResult(audio_codec="aac"),
            "standalone.aac",
        )

        self.assertTrue(plan.requires_ffmpeg)
        self.assertEqual(plan.audio_args, ("-c:a", "copy"))

    def test_m4a_encodes_non_aac_fallback(self):
        plan = build_finalization_plan(
            {"format": "m4a", "audio_quality": "best"},
            MediaProbeResult(audio_codec="opus"),
            "fallback.webm",
        )

        self.assertTrue(plan.requires_ffmpeg)
        self.assertEqual(plan.audio_args, ("-c:a", "aac", "-b:a", "192k"))

    def test_compatible_webm_container_does_not_require_remux(self):
        plan = build_finalization_plan(
            {"format": "webm", "audio_quality": "best"},
            MediaProbeResult(
                audio_codec="opus",
                video_codec="vp9",
            ),
            "source.webm",
        )

        self.assertFalse(plan.requires_ffmpeg)
        self.assertEqual(plan.video_args, ("-c:v", "copy"))
        self.assertEqual(plan.audio_args, ("-c:a", "copy"))

    def test_stream_bitrate_takes_priority_over_ytdlp_container_average(self):
        plan = build_finalization_plan(
            {
                "format": "mp4",
                "audio_quality": "128k",
                "_selected_audio_bitrate": 129_472,
            },
            MediaProbeResult(
                audio_codec="aac",
                audio_bit_rate=127_999,
                video_codec="av1",
            ),
        )

        self.assertEqual(plan.audio_args, ("-c:a", "copy"))
        self.assertFalse(plan.requires_ffmpeg)

    def test_ytdlp_bitrate_is_fallback_when_stream_bitrate_is_missing(self):
        plan = build_finalization_plan(
            {
                "format": "mp4",
                "audio_quality": "128k",
                "_selected_audio_bitrate": 129_472,
            },
            MediaProbeResult(
                audio_codec="aac",
                audio_bit_rate=None,
                video_codec="av1",
            ),
        )

        self.assertEqual(plan.audio_args, ("-c:a", "aac", "-b:a", "128k"))
        self.assertTrue(plan.requires_ffmpeg)

    def test_worst_compatible_source_is_copied_without_reencoding(self):
        for target, codec in (("mp4", "aac"), ("webm", "opus"), ("mkv", "opus")):
            with self.subTest(target=target):
                plan = build_finalization_plan(
                    {"format": target, "audio_quality": "worst"},
                    MediaProbeResult(
                        audio_codec=codec,
                        video_codec="h264" if target == "mp4" else "vp9",
                        video_pixel_format="yuv420p",
                    ),
                )
                self.assertEqual(plan.audio_args, ("-c:a", "copy"))

    def test_video_audio_is_copied_under_cap_and_encoded_over_cap(self):
        cases = (("mp4", "aac"), ("webm", "opus"), ("mkv", "opus"))
        for target, codec in cases:
            with self.subTest(target=target, selected="under"):
                copied = build_finalization_plan(
                    {
                        "format": target,
                        "audio_quality": "192k",
                        "_selected_audio_bitrate": 136_500,
                    },
                    MediaProbeResult(
                        audio_codec=codec,
                        video_codec="h264" if target == "mp4" else "vp9",
                        video_pixel_format="yuv420p",
                    ),
                )
                self.assertEqual(copied.audio_args, ("-c:a", "copy"))

            with self.subTest(target=target, selected="over"):
                encoded = build_finalization_plan(
                    {
                        "format": target,
                        "audio_quality": "96k",
                        "_selected_audio_bitrate": 136_500,
                    },
                    MediaProbeResult(
                        audio_codec=codec,
                        video_codec="h264" if target == "mp4" else "vp9",
                        video_pixel_format="yuv420p",
                    ),
                )
                expected_codec = "aac" if target == "mp4" else "libopus"
                self.assertEqual(
                    encoded.audio_args,
                    ("-c:a", expected_codec, "-b:a", "96k"),
                )

    def test_normalization_quality_and_compatibility_share_one_plan(self):
        plan = build_finalization_plan(
            {
                "format": "mp4",
                "audio_quality": "128k",
                "normalize_audio": True,
                "universal_compatibility": True,
            },
            MediaProbeResult(
                audio_sample_rate=48000,
                audio_codec="opus",
                video_codec="vp9",
                video_pixel_format="yuv444p",
            ),
        )
        command = build_finalization_command(
            "ffmpeg.exe", "input.mkv", "output.mp4", plan
        )

        self.assertEqual(command[command.index("-c:v") + 1], "libx264")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")
        self.assertEqual(command[command.index("-b:a") + 1], "128k")
        self.assertEqual(
            command[command.index("-af") + 1],
            "loudnorm=I=-14:TP=-1,aresample=48000",
        )
        self.assertEqual(command.count("-i"), 1)

    def test_mp3_uses_one_audio_only_encoding_pass(self):
        plan = build_finalization_plan(
            {"format": "mp3", "audio_quality": "320k"},
            MediaProbeResult(audio_sample_rate=48000, audio_codec="opus"),
        )
        command = build_finalization_command(
            "ffmpeg.exe", "input.webm", "output.mp3", plan
        )

        self.assertIn("-vn", command)
        self.assertEqual(command[command.index("-c:a") + 1], "libmp3lame")
        self.assertEqual(command[command.index("-b:a") + 1], "320k")


class FinalizationPipelineTests(unittest.TestCase):
    def test_video_only_compatible_non_webm_source_is_copy_remuxed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "silent.mp4"
            ffmpeg = root / "ffmpeg.exe"
            for path in (source, ffmpeg):
                path.write_bytes(b"source")

            commands = []

            def fake_run(command, **_kwargs):
                commands.append(command)
                Path(command[-1]).write_bytes(b"finished")
                return FfmpegExecutionResult(True)

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                side_effect=[
                    MediaProbeResult(video_codec="vp9"),
                    MediaProbeResult(video_codec="vp9"),
                ],
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "webm"},
                    str(ffmpeg),
                )

            self.assertTrue(result.success)
            self.assertEqual(Path(result.output_path).suffix, ".webm")
            self.assertEqual(commands[0][commands[0].index("-c:v") + 1], "copy")
            self.assertEqual(commands[0][commands[0].index("-c:a") + 1], "copy")

    def test_compatible_audio_and_video_in_mkv_are_copy_remuxed_to_webm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "compatible.mkv"
            ffmpeg = root / "ffmpeg.exe"
            for path in (source, ffmpeg):
                path.write_bytes(b"source")

            commands = []

            def fake_run(command, **_kwargs):
                commands.append(command)
                Path(command[-1]).write_bytes(b"finished")
                return FfmpegExecutionResult(True)

            compatible_probe = MediaProbeResult(
                audio_codec="opus",
                video_codec="vp9",
            )
            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                side_effect=[compatible_probe, compatible_probe],
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "webm"},
                    str(ffmpeg),
                )

            self.assertTrue(result.success)
            self.assertEqual(Path(result.output_path).suffix, ".webm")
            self.assertEqual(commands[0][commands[0].index("-c:v") + 1], "copy")
            self.assertEqual(commands[0][commands[0].index("-c:a") + 1], "copy")

    def test_webm_conversion_rejects_lost_source_audio(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "with-audio.mp4"
            ffmpeg = root / "ffmpeg.exe"
            for path in (source, ffmpeg):
                path.write_bytes(b"source")

            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"finished")
                return FfmpegExecutionResult(True)

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                side_effect=[
                    MediaProbeResult(
                        audio_codec="aac",
                        video_codec="h264",
                    ),
                    MediaProbeResult(video_codec="vp9"),
                ],
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "webm"},
                    str(ffmpeg),
                )

            self.assertFalse(result.success)
            self.assertIn("WebM codecs", result.error)
            self.assertTrue(source.exists())
            self.assertEqual(list(downloads.iterdir()), [])

    def test_completed_file_appears_in_download_folder_only_after_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "title.webm"
            ffmpeg = root / "ffmpeg.exe"
            ffprobe = root / "ffprobe.exe"
            for path in (source, ffmpeg, ffprobe):
                path.write_bytes(b"source")

            source_probe = MediaProbeResult(
                audio_sample_rate=48000,
                audio_codec="opus",
            )
            output_probe = MediaProbeResult(
                audio_sample_rate=48000,
                audio_codec="mp3",
            )

            def fake_run(command, **_kwargs):
                self.assertEqual(list(downloads.iterdir()), [])
                Path(command[-1]).write_bytes(b"finished")
                return FfmpegExecutionResult(True)

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                side_effect=[source_probe, output_probe],
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "mp3", "audio_quality": "best"},
                    str(ffmpeg),
                )

            self.assertTrue(result.success)
            self.assertEqual(Path(result.output_path).parent, downloads)
            self.assertEqual(Path(result.output_path).read_bytes(), b"finished")
            self.assertFalse(source.exists())

    def test_failure_keeps_source_in_workspace_and_downloads_empty(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "title.webm"
            ffmpeg = root / "ffmpeg.exe"
            ffprobe = root / "ffprobe.exe"
            for path in (source, ffmpeg, ffprobe):
                path.write_bytes(b"source")

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                return_value=MediaProbeResult(
                    audio_sample_rate=48000,
                    audio_codec="opus",
                ),
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                return_value=FfmpegExecutionResult(False, "encode failed"),
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "mp3"},
                    str(ffmpeg),
                )

            self.assertFalse(result.success)
            self.assertTrue(source.exists())
            self.assertEqual(list(downloads.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
