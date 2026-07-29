import json
import os
from pathlib import Path
import sys
import tempfile
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

from core.download.media_probe import probe_media_file


class MediaProbeTests(unittest.TestCase):
    def test_uses_sibling_ffprobe_json_when_available(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "input.mkv")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            ffprobe_path = Path(directory, "ffprobe.exe")
            for path in (input_path, ffmpeg_path, ffprobe_path):
                path.write_bytes(b"test")

            completed = SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "streams": [
                            {
                                "codec_type": "video",
                                "codec_name": "vp9",
                            },
                            {
                                "codec_type": "audio",
                                "codec_name": "opus",
                                "sample_rate": "48000",
                            },
                        ]
                    }
                ),
                stderr="",
            )

            with patch(
                "core.download.media_probe.subprocess.run",
                return_value=completed,
            ) as run:
                result = probe_media_file(str(input_path), str(ffmpeg_path))

            self.assertEqual(result.audio_sample_rate, 48000)
            self.assertEqual(result.audio_codec, "opus")
            self.assertEqual(result.video_codec, "vp9")
            self.assertEqual(run.call_args.args[0][0], str(ffprobe_path))

    def test_returns_empty_result_without_required_sibling_ffprobe(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "input.mp4")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            input_path.write_bytes(b"test")
            ffmpeg_path.write_bytes(b"test")

            with patch(
                "core.download.media_probe.subprocess.run",
            ) as run:
                result = probe_media_file(str(input_path), str(ffmpeg_path))

            self.assertIsNone(result.audio_sample_rate)
            self.assertIsNone(result.audio_codec)
            self.assertIsNone(result.video_codec)
            run.assert_not_called()

    def test_does_not_fall_back_when_ffprobe_result_is_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory, "input.mkv")
            ffmpeg_path = Path(directory, "ffmpeg.exe")
            ffprobe_path = Path(directory, "ffprobe.exe")
            for path in (input_path, ffmpeg_path, ffprobe_path):
                path.write_bytes(b"test")

            ffprobe_completed = SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "streams": [
                            {
                                "codec_type": "audio",
                                "codec_name": "opus",
                                "sample_rate": "48000",
                            },
                            {
                                "codec_type": "video",
                                "codec_name": "",
                            },
                        ]
                    }
                ),
                stderr="",
            )
            with patch(
                "core.download.media_probe.subprocess.run",
                return_value=ffprobe_completed,
            ) as run:
                result = probe_media_file(str(input_path), str(ffmpeg_path))

            self.assertEqual(result.audio_sample_rate, 48000)
            self.assertEqual(result.audio_codec, "opus")
            self.assertIsNone(result.video_codec)
            self.assertEqual(run.call_count, 1)


if __name__ == "__main__":
    unittest.main()
