import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin.ffmpeg_install import install_ffmpeg_from_zip


class BinFfmpegInstallTests(unittest.TestCase):
    def test_install_ffmpeg_from_zip_extracts_binary_and_saves_version(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            final_path = Path(tmpdir) / "ffmpeg.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"binary")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(final_path),
                "2026.07.01",
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
                lambda: {"yt-dlp": "2026"},
                lambda versions: saved.append(versions) or True,
            )

            self.assertTrue(result)
            self.assertEqual(final_path.read_bytes(), b"binary")

        self.assertEqual(saved[0]["ffmpeg"], "2026.07.01")
        self.assertIn("last_check", saved[0])

    def test_install_ffmpeg_from_zip_returns_false_without_matching_member(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            final_path = Path(tmpdir) / "ffmpeg.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("docs/readme.txt", "ignored")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(final_path),
                "2026.07.01",
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
                lambda: {},
                lambda versions: saved.append(versions) or True,
            )

            self.assertFalse(result)
            self.assertFalse(final_path.exists())
            self.assertEqual(saved, [])


if __name__ == "__main__":
    unittest.main()