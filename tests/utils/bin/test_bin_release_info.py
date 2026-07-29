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

from utils.bin.release_info import (
    ffmpeg_release_info,
    release_asset_info,
    normalize_release_tag,
    quickjs_release_info,
    release_version_from_published_or_tag,
    ytdlp_release_info,
)


class BinReleaseInfoTests(unittest.TestCase):
    def test_normalize_release_tag_removes_v_prefix(self):
        self.assertEqual(normalize_release_tag("v2024.01.30"), "2024.01.30")
        self.assertEqual(normalize_release_tag(None), "")

    def test_release_version_from_published_or_tag_prefers_published_date(self):
        data = {"published_at": "2026-07-01T12:34:56Z", "tag_name": "latest"}

        self.assertEqual(release_version_from_published_or_tag(data), "2026.07.01")

    def test_release_version_from_published_or_tag_falls_back_to_tag(self):
        self.assertEqual(
            release_version_from_published_or_tag({"tag_name": "v1.2.3"}),
            "1.2.3",
        )

    def test_ytdlp_release_info_returns_version_and_url(self):
        data = {
            "tag_name": "v2024.01.30",
            "assets": [{
                "name": "yt-dlp.exe",
                "browser_download_url": "url",
                "digest": "sha256:" + "a" * 64,
            }],
        }

        self.assertEqual(
            ytdlp_release_info(data, "yt-dlp.exe"),
            ("2024.01.30", "url", "sha256:" + "a" * 64),
        )

    def test_ytdlp_release_info_returns_none_without_asset(self):
        self.assertEqual(
            ytdlp_release_info({"tag_name": "v1", "assets": []}, "yt-dlp.exe"),
            (None, None, None),
        )

    def test_ffmpeg_release_info_uses_published_date_and_matching_asset(self):
        data = {
            "published_at": "2026-07-01T12:34:56Z",
            "assets": [
                {
                    "name": "ffmpeg-master-latest-win64-gpl.zip",
                    "browser_download_url": "url",
                    "digest": "sha256:" + "b" * 64,
                },
            ],
        }

        self.assertEqual(
            ffmpeg_release_info(data, "ffmpeg-master-latest-win64-gpl.zip"),
            ("2026.07.01", "url", "sha256:" + "b" * 64),
        )

    def test_quickjs_release_info_returns_exact_asset(self):
        data = {
            "tag_name": "v0.9.0",
            "assets": [{
                "name": "qjs-windows-x86_64.exe",
                "browser_download_url": "url",
                "digest": "sha256:" + "c" * 64,
            }],
        }

        self.assertEqual(
            quickjs_release_info(data, "qjs-windows-x86_64.exe"),
            ("0.9.0", "url", "sha256:" + "c" * 64),
        )

    def test_release_asset_info_returns_url_and_digest(self):
        data = {
            "assets": [{
                "name": "tool.exe",
                "browser_download_url": "url",
                "digest": "sha256:" + "d" * 64,
            }],
        }

        self.assertEqual(
            release_asset_info(data, exact_name="tool.exe"),
            ("url", "sha256:" + "d" * 64),
        )


if __name__ == "__main__":
    unittest.main()
