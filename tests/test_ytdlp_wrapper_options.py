import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.ytdlp.wrapper import YtDlpWrapper


class FakeCompletedProcess:
    def __init__(self, stdout=None, stderr="", returncode=0):
        self.stdout = stdout if stdout is not None else json.dumps({"id": "ok"})
        self.stderr = stderr
        self.returncode = returncode


class YtDlpWrapperOptionTests(unittest.TestCase):
    def test_build_command_starts_with_newline_option(self):
        cmd = YtDlpWrapper("yt-dlp.exe")._build_command("https://example.invalid", {}, False)

        self.assertEqual(cmd[:2], ["yt-dlp.exe", "--newline"])

    def test_build_command_maps_recode_audio_quality_and_postprocessor_args(self):
        cmd = YtDlpWrapper("yt-dlp.exe")._build_command(
            "https://example.invalid",
            {
                "format": "bestvideo+worstaudio/best",
                "recode_video": "webm",
                "postprocessor_args": {"ffmpeg": ["-b:a", "48k"]},
                "extract_audio": True,
                "audio_format": "mp3",
                "audio_quality": "320k",
            },
            False,
        )

        self.assertIn("--recode-video", cmd)
        self.assertEqual(cmd[cmd.index("--recode-video") + 1], "webm")
        self.assertIn("--audio-quality", cmd)
        self.assertEqual(cmd[cmd.index("--audio-quality") + 1], "320k")
        self.assertIn("--postprocessor-args", cmd)
        self.assertIn("ffmpeg:-b:a 48k", cmd)

    def test_extract_flat_true_adds_flat_playlist(self):
        captured = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            return FakeCompletedProcess()

        with patch.object(subprocess, "run", side_effect=fake_run):
            info, success = YtDlpWrapper("yt-dlp.exe").extract_info(
                "https://example.invalid",
                options={"extract_flat": True},
            )

        self.assertTrue(success)
        self.assertEqual(info["id"], "ok")
        self.assertIn("--flat-playlist", captured["args"])

    def test_extract_flat_in_playlist_does_not_add_flat_playlist(self):
        captured = {}

        def fake_run(args, **kwargs):
            captured["args"] = args
            return FakeCompletedProcess()

        with patch.object(subprocess, "run", side_effect=fake_run):
            _, success = YtDlpWrapper("yt-dlp.exe").extract_info(
                "https://example.invalid",
                options={"extract_flat": "in_playlist"},
            )

        self.assertTrue(success)
        self.assertNotIn("--flat-playlist", captured["args"])


if __name__ == "__main__":
    unittest.main()
