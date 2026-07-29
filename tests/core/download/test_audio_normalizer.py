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

from core.download.normalizer import (
    build_normalization_command,
    normalize_media_file,
    normalized_output_path,
)
from core.download.media_probe import MediaProbeResult


class AudioNormalizerCommandTests(unittest.TestCase):
    def test_mp4_copies_video_and_reencodes_only_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.mp4",
            "output.mp4",
            "mp4",
            "worst",
            audio_sample_rate=48000,
        )

        self.assertIn("copy", command)
        self.assertIn("aac", command)
        self.assertIn("48k", command)
        self.assertEqual(
            command[command.index("-af") + 1],
            "loudnorm=I=-14:TP=-1,aresample=48000",
        )
        self.assertIn("+faststart", command)

    def test_mkv_uses_copy_video_and_aac_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.mkv",
            "output.mkv",
            "mkv",
            "128k",
            audio_sample_rate=48000,
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
            audio_sample_rate=48000,
        )

        self.assertEqual(command[command.index("-c:v") + 1], "libvpx-vp9")
        self.assertEqual(command[command.index("-crf") + 1], "30")
        self.assertEqual(command[command.index("-b:v") + 1], "0")
        self.assertEqual(command[command.index("-deadline") + 1], "good")
        self.assertEqual(command[command.index("-c:a") + 1], "libopus")
        self.assertIn("160k", command)

    def test_existing_webm_copies_video_and_reencodes_opus_audio(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.webm",
            "output.webm",
            "webm",
            "worst",
            audio_sample_rate=48000,
        )

        self.assertEqual(command[command.index("-c:v") + 1], "copy")
        self.assertEqual(command[command.index("-c:a") + 1], "libopus")

    def test_webm_uses_actual_video_codec_instead_of_input_extension(self):
        copy_command = build_normalization_command(
            "ffmpeg.exe",
            "input.mkv",
            "output.webm",
            "webm",
            "best",
            audio_sample_rate=48000,
            video_codec="vp9",
        )
        transcode_command = build_normalization_command(
            "ffmpeg.exe",
            "input.webm",
            "output.webm",
            "webm",
            "best",
            audio_sample_rate=48000,
            video_codec="h264",
        )

        self.assertEqual(copy_command[copy_command.index("-c:v") + 1], "copy")
        self.assertEqual(
            transcode_command[transcode_command.index("-c:v") + 1],
            "libvpx-vp9",
        )

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
                    audio_sample_rate=48000,
                )
                self.assertEqual(command[command.index("-c:a") + 1], codec)
                self.assertNotIn("-c:v", command)
                self.assertEqual(
                    command[command.index("-af") + 1],
                    "loudnorm=I=-14:TP=-1,aresample=48000",
                )

    def test_output_path_uses_requested_extension(self):
        output = Path(normalized_output_path("C:/Downloads/title.m4a", "mp3"))

        self.assertEqual(output.stem, "title")
        self.assertEqual(output.suffix, ".mp3")

    def test_normalization_restores_source_sample_rate_in_same_filter_chain(self):
        command = build_normalization_command(
            "ffmpeg.exe",
            "input.webm",
            "output.wav",
            "wav",
            "128k",
            audio_sample_rate=48000,
        )

        audio_filter = command[command.index("-af") + 1]
        self.assertEqual(
            audio_filter,
            "loudnorm=I=-14:TP=-1,aresample=48000",
        )

    def test_command_rejects_missing_sample_rate(self):
        with self.assertRaisesRegex(ValueError, "sample rate is required"):
            build_normalization_command(
                "ffmpeg.exe",
                "input.webm",
                "output.wav",
                "wav",
                "128k",
            )

    def test_normalization_uses_probed_stream_properties(self):
        class CompletedProcess:
            returncode = 0
            stderr = io.StringIO("")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.webm")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")
            captured_command = []

            def start_process(command, **_kwargs):
                captured_command.extend(command)
                Path(command[-1]).write_bytes(b"normalized")
                return CompletedProcess()

            with patch(
                "core.download.normalizer.probe_media_file",
                side_effect=[
                    MediaProbeResult(
                        audio_sample_rate=48000,
                        video_codec="h264",
                    ),
                    MediaProbeResult(audio_sample_rate=48000),
                ],
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
                result = normalize_media_file(
                    str(input_path),
                    {"format": "webm", "audio_quality": "best"},
                    str(ffmpeg_path),
                )

            self.assertTrue(result.success)
            self.assertEqual(
                captured_command[captured_command.index("-af") + 1],
                "loudnorm=I=-14:TP=-1,aresample=48000",
            )
            self.assertEqual(
                captured_command[captured_command.index("-c:v") + 1],
                "libvpx-vp9",
            )

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

            with patch(
                "core.download.normalizer.probe_media_file",
                return_value=MediaProbeResult(audio_sample_rate=48000),
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
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

            with patch(
                "core.download.normalizer.probe_media_file",
                return_value=MediaProbeResult(audio_sample_rate=48000),
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ):
                result = normalize_media_file(
                    str(input_path),
                    {"format": "mp4", "audio_quality": "worst"},
                    str(ffmpeg_path),
                    stop_check=lambda: True,
                )

            self.assertTrue(result.paused)
            self.assertFalse(input_path.exists())
            self.assertEqual(list(Path(directory).glob("*.normalize.mp4")), [])

    def test_missing_input_sample_rate_fails_without_starting_ffmpeg(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.wav")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            with patch(
                "core.download.normalizer.probe_media_file",
                return_value=MediaProbeResult(),
            ), patch("core.download.ffmpeg_process.subprocess.Popen") as popen:
                result = normalize_media_file(
                    str(input_path),
                    {"format": "wav", "audio_quality": "best"},
                    str(ffmpeg_path),
                )

            self.assertFalse(result.success)
            self.assertIn("could not be determined", result.error)
            popen.assert_not_called()
            self.assertFalse(input_path.exists())

    def test_output_sample_rate_mismatch_fails_before_replacing_source(self):
        class CompletedProcess:
            returncode = 0
            stderr = io.StringIO("")

            def poll(self):
                return self.returncode

        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "title.wav")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"downloaded")
            ffmpeg_path.write_bytes(b"executable")

            def start_process(command, **_kwargs):
                Path(command[-1]).write_bytes(b"normalized")
                return CompletedProcess()

            with patch(
                "core.download.normalizer.probe_media_file",
                side_effect=[
                    MediaProbeResult(audio_sample_rate=48000),
                    MediaProbeResult(audio_sample_rate=192000),
                ],
            ), patch(
                "core.download.ffmpeg_process.subprocess.Popen",
                side_effect=start_process,
            ), patch("core.download.normalizer.os.replace") as replace:
                result = normalize_media_file(
                    str(input_path),
                    {"format": "wav", "audio_quality": "best"},
                    str(ffmpeg_path),
                )

            self.assertFalse(result.success)
            self.assertIn("48000 Hz to 192000 Hz", result.error)
            replace.assert_not_called()
            self.assertFalse(input_path.exists())
            self.assertEqual(list(Path(directory).glob("*.normalize.wav")), [])


if __name__ == "__main__":
    unittest.main()
