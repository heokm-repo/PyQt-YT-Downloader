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
from core.download.finalization_pipeline import finalize_and_commit_download
from core.download.finalization_policy import build_finalization_plan
from core.download.finalization_verification import verify_finalized_output
from core.download.media_probe import MediaProbeResult


class FinalizationVerificationTests(unittest.TestCase):
    def test_audio_only_output_requires_a_verified_audio_stream(self):
        source = MediaProbeResult(audio_codec="opus", audio_sample_rate=48000)
        plan = build_finalization_plan({"format": "mp3"}, source)

        error = verify_finalized_output(plan, source, MediaProbeResult())

        self.assertEqual(error, "Final audio stream could not be verified")

    def test_normalized_output_must_preserve_source_sample_rate(self):
        source = MediaProbeResult(audio_codec="opus", audio_sample_rate=48000)
        output = MediaProbeResult(audio_codec="mp3", audio_sample_rate=192000)
        plan = build_finalization_plan(
            {"format": "mp3", "normalize_audio": True},
            source,
        )

        error = verify_finalized_output(plan, source, output)

        self.assertEqual(error, "Final audio sample rate did not match the source")

    def test_video_output_requires_a_verified_video_stream(self):
        source = MediaProbeResult(video_codec="h264", audio_codec="aac")
        output = MediaProbeResult(audio_codec="aac")
        plan = build_finalization_plan({"format": "mp4"}, source)

        error = verify_finalized_output(plan, source, output)

        self.assertEqual(error, "Final video stream could not be verified")

    def test_mp3_output_accepts_matching_audio_and_sample_rate(self):
        source = MediaProbeResult(audio_codec="opus", audio_sample_rate=48000)
        output = MediaProbeResult(audio_codec="mp3", audio_sample_rate=48000)
        plan = build_finalization_plan({"format": "mp3"}, source)

        self.assertIsNone(verify_finalized_output(plan, source, output))


class FinalizationVerificationIntegrationTests(unittest.TestCase):
    def test_unverifiable_noop_output_is_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "title.mp4"
            ffmpeg = root / "ffmpeg.exe"
            source.write_bytes(b"unverifiable source")
            ffmpeg.write_bytes(b"binary")

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                return_value=MediaProbeResult(),
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
            ) as run_ffmpeg:
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "mp4", "audio_quality": "worst"},
                    str(ffmpeg),
                )

            self.assertFalse(result.success)
            self.assertIn("video stream", result.error)
            self.assertTrue(source.exists())
            self.assertEqual(list(downloads.iterdir()), [])
            run_ffmpeg.assert_not_called()

    def test_unverifiable_encoded_output_is_not_published(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = root / ".ytdl_temp" / "task"
            downloads = root / "downloads"
            workspace.mkdir(parents=True)
            downloads.mkdir()
            source = workspace / "title.webm"
            ffmpeg = root / "ffmpeg.exe"
            source.write_bytes(b"source")
            ffmpeg.write_bytes(b"binary")

            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"invalid output")
                return FfmpegExecutionResult(True)

            with patch(
                "core.download.finalization_pipeline.probe_media_file",
                side_effect=[
                    MediaProbeResult(audio_codec="opus", audio_sample_rate=48000),
                    MediaProbeResult(),
                ],
            ), patch(
                "core.download.finalization_pipeline.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_and_commit_download(
                    str(source),
                    str(workspace),
                    str(downloads),
                    {"format": "mp3"},
                    str(ffmpeg),
                )

            self.assertFalse(result.success)
            self.assertIn("audio stream", result.error)
            self.assertTrue(source.exists())
            self.assertEqual(list(downloads.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
