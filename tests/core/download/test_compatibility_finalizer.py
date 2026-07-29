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

from core.download.compatibility_finalizer import (
    build_compatibility_command,
    finalize_mp4_compatibility,
)
from core.download.ffmpeg_process import FfmpegExecutionResult
from core.download.media_probe import MediaProbeResult


class CompatibilityFinalizerTests(unittest.TestCase):
    def test_command_copies_already_compatible_streams(self):
        command = build_compatibility_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.mp4",
            MediaProbeResult(
                audio_codec="aac",
                video_codec="h264",
                video_pixel_format="yuv420p",
            ),
        )

        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
        self.assertIn("+faststart", command)

    def test_command_encodes_incompatible_video_and_audio(self):
        command = build_compatibility_command(
            "ffmpeg.exe",
            "input.webm",
            "output.mp4",
            MediaProbeResult(
                audio_codec="opus",
                video_codec="vp9",
                video_pixel_format="yuv444p",
            ),
        )

        self.assertEqual(command[command.index("-c:v") + 1], "libx264")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")
        self.assertEqual(command[command.index("-pix_fmt") + 1], "yuv420p")

    def test_finalizer_verifies_and_commits_compatible_output(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "input.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            ffprobe_path = Path(directory, "ffprobe.exe")
            for path in (input_path, ffmpeg_path, ffprobe_path):
                path.write_bytes(b"test")

            source_probe = MediaProbeResult(
                audio_codec="opus",
                video_codec="vp9",
                video_pixel_format="yuv420p",
            )
            output_probe = MediaProbeResult(
                audio_codec="aac",
                video_codec="h264",
                video_pixel_format="yuv420p",
            )

            def fake_run(command, **_kwargs):
                Path(command[-1]).write_bytes(b"converted")
                return FfmpegExecutionResult(True)

            with patch(
                "core.download.compatibility_finalizer.probe_media_file",
                side_effect=[source_probe, output_probe],
            ), patch(
                "core.download.compatibility_finalizer.run_ffmpeg_command",
                side_effect=fake_run,
            ):
                result = finalize_mp4_compatibility(
                    str(input_path), str(ffmpeg_path)
                )

            self.assertTrue(result.success)
            self.assertEqual(Path(result.output_path).read_bytes(), b"converted")


if __name__ == "__main__":
    unittest.main()
