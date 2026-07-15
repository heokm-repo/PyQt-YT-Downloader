import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.normalizer import (
    build_normalization_command,
    normalize_media_file,
    normalized_output_path,
)


class AudioNormalizerCommandTests(unittest.TestCase):
    def test_mp4_copies_video_and_reencodes_only_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.mp4",
            "mp4",
            "worst",
        )

        self.assertIn("copy", command)
        self.assertIn("aac", command)
        self.assertIn("48k", command)
        self.assertIn("loudnorm=I=-14:TP=-1", command)
        self.assertIn("+faststart", command)

    def test_mkv_uses_copy_video_and_aac_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.mkv",
            "output.mkv",
            "mkv",
            "128k",
        )

        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "aac")
        self.assertIn("128k", command)

    def test_webm_conversion_uses_vp9_and_opus(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.webm",
            "webm",
            "best",
        )

        self.assertEqual(command[command.index("-c:v") + 1], "libvpx-vp9")
        self.assertEqual(command[command.index("-c:a") + 1], "libopus")
        self.assertIn("160k", command)

    def test_existing_webm_copies_video_and_reencodes_opus_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.webm",
            "output.webm",
            "webm",
            "worst",
        )

        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "libopus")

    def test_audio_formats_use_target_specific_codecs(self):
        expectations = {
            "mp3": "libmp3lame",
            "m4a": "aac",
            "wav": "pcm_s16le",
        }

        for target_format, codec in expectations.items():
            with self.subTest(target_format=target_format):
                command = build_normalization_command(
                    "ffmpeg.exe",
                    "input.m4a",
                    f"output.{target_format}",
                    target_format,
                    "worst",
                )
                self.assertEqual(command[command.index("-c:a") + 1], codec)
                self.assertNotIn("-c:v", command)
                self.assertIn("loudnorm=I=-14:TP=-1", command)

    def test_output_path_uses_requested_extension(self):
        output = Path(normalized_output_path("C:/Downloads/title.m4a", "mp3"))

        self.assertEqual(output.stem, "title")
        self.assertEqual(output.suffix, ".mp3")

    def test_ffmpeg_failure_removes_downloaded_and_temporary_files(self):
        class FailedProcess:
            returncode = 1
            stderr = io.StringIO("normalization failed\n")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"incomplete")
                return FailedProcess()

            with patch("core.download.normalizer.subprocess.Popen", side_effect=start_process):
                result = normalize_media_file(
                    str(input_path),
                    {"format": "mp4", "audio_quality": "worst"},
                    str(ffmpeg_path),
                )

            self.assertFalse(result.success)
            self.assertFalse(input_path.exists())
            self.assertEqual(list(Path(directory).glob("*.normalize.mp4")), [])

    def test_cancellation_removes_downloaded_and_temporary_files(self):
        class RunningProcess:
            returncode = None
            stderr = io.StringIO("")

            def poll(self):
                return self.returncode

            def kill(self):
                self.returncode = -9

            def wait(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"incomplete")
                return RunningProcess()

            with patch("core.download.normalizer.subprocess.Popen", side_effect=start_process):
                result = normalize_media_file(
                    str(input_path),
                    {"format": "mp4", "audio_quality": "worst"},
                    str(ffmpeg_path),
                    stop_check=lambda: True,
                )

            self.assertTrue(result.paused)
            self.assertFalse(input_path.exists())
            self.assertEqual(list(Path(directory).glob("*.normalize.mp4")), [])


if __name__ == "__main__":
    unittest.main()
