import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.ytdlp.command import build_command
from core.ytdlp.wrapper import YtDlpWrapper


class YtDlpCommandTests(unittest.TestCase):
    def test_build_command_maps_paths_runtime_and_resume_options(self):
        cmd = build_command(
            "yt-dlp.exe",
            "fallback-ffmpeg.exe",
            "https://example.invalid/video",
            {
                "outtmpl": "%(title)s.%(ext)s",
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "remux_video": "mp4",
                "ffmpeg_location": "ffmpeg.exe",
                "noplaylist": True,
                "cookiefile": "cookies.txt",
                "js_runtimes": "quickjs:qjs.exe",
                "concurrent_fragment_downloads": 6,
                "home_path": "C:/Downloads",
                "temp_path": "C:/Downloads/.tmp",
                "overwrites": True,
            },
            is_resume=False,
        )

        self.assertEqual(cmd[:10], [
            "yt-dlp.exe",
            "--ignore-config",
            "--no-plugin-dirs",
            "--no-remote-components",
            "--encoding",
            "utf-8",
            "--newline",
            "--progress",
            "--print",
            "after_move:__YTDLP_FINAL_PATH__:%(filepath)s",
        ])
        print_templates = [
            cmd[index + 1]
            for index, argument in enumerate(cmd)
            if argument == "--print"
        ]
        self.assertEqual(
            print_templates,
            [
                "after_move:__YTDLP_FINAL_PATH__:%(filepath)s",
                "before_dl:__YTDLP_METADATA__:%()j",
            ],
        )
        self.assertIn("--output", cmd)
        self.assertEqual(cmd[cmd.index("--merge-output-format") + 1], "mp4")
        self.assertEqual(cmd[cmd.index("--remux-video") + 1], "mp4")
        self.assertEqual(cmd[cmd.index("--ffmpeg-location") + 1], "ffmpeg.exe")
        self.assertIn("--no-playlist", cmd)
        self.assertEqual(cmd[cmd.index("--cookies") + 1], "cookies.txt")
        self.assertEqual(cmd[cmd.index("--js-runtimes") + 1], "quickjs:qjs.exe")
        self.assertEqual(cmd[cmd.index("--concurrent-fragments") + 1], "6")
        self.assertIn("home:C:/Downloads", cmd)
        self.assertIn("temp:C:/Downloads/.tmp", cmd)
        self.assertIn("--force-overwrites", cmd)
        self.assertEqual(cmd[-2:], ["--", "https://example.invalid/video"])

    def test_build_command_resume_overrides_force_overwrites(self):
        cmd = build_command(
            "yt-dlp.exe",
            None,
            "https://example.invalid/video",
            {"overwrites": True},
            is_resume=True,
        )

        self.assertIn("--no-overwrites", cmd)
        self.assertNotIn("--force-overwrites", cmd)

    def test_build_command_combines_same_postprocessor_key_args(self):
        cmd = build_command(
            "yt-dlp.exe",
            None,
            "https://example.invalid/audio",
            {
                "postprocessor_args": {
                    "ExtractAudio+ffmpeg_o": ["-ac", "2", "-af", "loudnorm=I=-14:TP=-1"],
                },
            },
        )

        self.assertEqual(cmd.count("--postprocessor-args"), 1)
        self.assertIn(
            "ExtractAudio+ffmpeg_o:-ac 2 -af loudnorm=I=-14:TP=-1",
            cmd,
        )

    def test_wrapper_private_method_delegates_to_command_builder(self):
        wrapper = YtDlpWrapper("yt-dlp.exe", "ffmpeg.exe")
        cmd = wrapper._build_command("https://example.invalid/video", {"format": "best"})

        self.assertEqual(cmd[0], "yt-dlp.exe")
        self.assertEqual(cmd[cmd.index("--ffmpeg-location") + 1], "ffmpeg.exe")
        self.assertEqual(cmd[cmd.index("--format") + 1], "best")


if __name__ == "__main__":
    unittest.main()
