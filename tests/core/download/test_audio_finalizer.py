import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.audio_finalizer import (
    build_audio_finalization_command,
    finalize_video_audio_quality,
)
from core.download.media_probe import MediaProbeResult


class AudioFinalizerTests(unittest.TestCase):
    def test_command_copies_video_and_encodes_only_audio(self):
        command = build_audio_finalization_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.mp4",
            "mp4",
            "128k",
            48000,
        )

        self.assertEqual(command[command.index("-c") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")
        self.assertEqual(command[command.index("-b:a") + 1], "128k")
        self.assertEqual(command[command.index("-ar") + 1], "48000")
        self.assertNotIn("-af", command)
        self.assertIn("+faststart", command)

    def test_webm_best_copies_compatible_streams(self):
        command = build_audio_finalization_command(
            "ffmpeg.exe",
            "input.mkv",
            "output.webm",
            "webm",
            None,
            48000,
            video_codec="vp9",
            audio_codec="opus",
        )

        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "copy")
        self.assertNotIn("-b:a", command)

    def test_webm_best_transcodes_only_incompatible_streams(self):
        command = build_audio_finalization_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.webm",
            "webm",
            None,
            48000,
            video_codec="h264",
            audio_codec="aac",
        )

        self.assertEqual(
            command[command.index("-c:v") + 1],
            "libvpx-vp9",
        )
        self.assertEqual(command[command.index("-c:a") + 1], "libopus")
        self.assertEqual(command[command.index("-b:a") + 1], "160k")

    def test_existing_compatible_webm_best_skips_ffmpeg(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.webm")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            with patch(
                "core.download.audio_finalizer.probe_media_file",
                return_value=MediaProbeResult(
                    audio_sample_rate=48000,
                    audio_codec="opus",
                    video_codec="vp9",
                ),
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
            ) as popen:
                result = finalize_video_audio_quality(
                    str(input_path),
                    "webm",
                    None,
                    str(ffmpeg_path),
                )

            self.assertTrue(result.success)
            self.assertEqual(result.output_path, str(input_path))
            popen.assert_not_called()

    def test_success_atomically_replaces_source_after_sample_rate_verification(self):
        class CompletedProcess:
            returncode = 0
            stderr = io.StringIO("")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"finalized")
                return CompletedProcess()

            with patch(
                "core.download.audio_finalizer.probe_media_file",
                side_effect=[
                    MediaProbeResult(audio_sample_rate=48000),
                    MediaProbeResult(audio_sample_rate=48000),
                ],
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
                result = finalize_video_audio_quality(
                    str(input_path),
                    "mp4",
                    "128k",
                    str(ffmpeg_path),
                )

            self.assertTrue(result.success)
            self.assertEqual(result.output_path, str(input_path))
            self.assertEqual(input_path.read_bytes(), b"finalized")

    def test_ffmpeg_failure_keeps_downloaded_source_and_removes_temporary_file(self):
        class FailedProcess:
            returncode = 1
            stderr = io.StringIO("quality finalization failed\n")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.mkv")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"incomplete")
                return FailedProcess()

            with patch(
                "core.download.audio_finalizer.probe_media_file",
                return_value=MediaProbeResult(audio_sample_rate=48000),
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
                result = finalize_video_audio_quality(
                    str(input_path),
                    "mkv",
                    "48k",
                    str(ffmpeg_path),
                )

            self.assertFalse(result.success)
            self.assertEqual(input_path.read_bytes(), b"downloaded")
            self.assertEqual(
                list(Path(directory).glob("*.audio-quality.mkv")),
                [],
            )

    def test_output_sample_rate_mismatch_keeps_downloaded_source(self):
        class CompletedProcess:
            returncode = 0
            stderr = io.StringIO("")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"finalized")
                return CompletedProcess()

            with patch(
                "core.download.audio_finalizer.probe_media_file",
                side_effect=[
                    MediaProbeResult(audio_sample_rate=48000),
                    MediaProbeResult(audio_sample_rate=44100),
                ],
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
                result = finalize_video_audio_quality(
                    str(input_path),
                    "mp4",
                    "128k",
                    str(ffmpeg_path),
                )

            self.assertFalse(result.success)
            self.assertIn("48000 Hz to 44100 Hz", result.error)
            self.assertEqual(input_path.read_bytes(), b"downloaded")


if __name__ == "__main__":
    unittest.main()
