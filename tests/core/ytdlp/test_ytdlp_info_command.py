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

from core.ytdlp.info_command import build_extract_info_command


class YtDlpInfoCommandTests(unittest.TestCase):
    def test_build_extract_info_command_starts_with_dump_json_options(self):
        cmd = build_extract_info_command("yt-dlp.exe", "https://example.invalid/video")

        self.assertEqual(cmd, [
            "yt-dlp.exe",
            "--ignore-config",
            "--no-plugin-dirs",
            "--no-remote-components",
            "--encoding",
            "utf-8",
            "--dump-json",
            "--no-warnings",
            "--",
            "https://example.invalid/video",
        ])

    def test_extract_flat_true_adds_flat_playlist(self):
        cmd = build_extract_info_command(
            "yt-dlp.exe",
            "https://example.invalid/playlist",
            {"extract_flat": True},
        )

        self.assertIn("--flat-playlist", cmd)

    def test_dump_single_json_replaces_per_entry_dump(self):
        cmd = build_extract_info_command(
            "yt-dlp.exe",
            "https://example.invalid/playlist",
            {"extract_flat": True, "dump_single_json": True},
        )

        self.assertIn("--dump-single-json", cmd)
        self.assertNotIn("--dump-json", cmd)

    def test_extract_flat_in_playlist_does_not_add_flat_playlist(self):
        cmd = build_extract_info_command(
            "yt-dlp.exe",
            "https://example.invalid/playlist",
            {"extract_flat": "in_playlist"},
        )

        self.assertNotIn("--flat-playlist", cmd)

    def test_maps_supported_metadata_options(self):
        cmd = build_extract_info_command(
            "yt-dlp.exe",
            "https://example.invalid/video",
            {
                "noplaylist": True,
                "format": "best",
                "format_sort": "res:1080",
                "cookiefile": "cookies.txt",
                "js_runtimes": "node:C:/node.exe",
            },
        )

        self.assertIn("--no-playlist", cmd)
        self.assertEqual(cmd[cmd.index("--format") + 1], "best")
        self.assertEqual(cmd[cmd.index("--format-sort") + 1], "res:1080")
        self.assertEqual(cmd[cmd.index("--cookies") + 1], "cookies.txt")
        self.assertEqual(cmd[cmd.index("--js-runtimes") + 1], "node:C:/node.exe")
        self.assertEqual(cmd[-2:], ["--", "https://example.invalid/video"])


if __name__ == "__main__":
    unittest.main()
