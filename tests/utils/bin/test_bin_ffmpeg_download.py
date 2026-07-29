import os
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin.ffmpeg_download import download_and_install_ffmpeg_zip


class BinFfmpegDownloadTests(unittest.TestCase):
    def test_download_and_install_ffmpeg_zip_downloads_installs_and_cleans_temp_zip(self):
        install_calls = []
        progress = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                self.assertEqual(url, "https://example.test/ffmpeg.zip")
                Path(dest_path).write_bytes(b"zip")
                progress_callback(10, 100)
                return True

            def fake_install(zip_path, ffmpeg_path, ffprobe_path, version, ffmpeg_suffixes, ffprobe_suffixes, load_versions, save_versions):
                install_calls.append((zip_path, ffmpeg_path, ffprobe_path, version))
                Path(ffmpeg_path).write_text("ffmpeg", encoding="utf-8")
                Path(ffprobe_path).write_text("ffprobe", encoding="utf-8")
                return True

            result = download_and_install_ffmpeg_zip(
                "2026.07.01",
                "https://example.test/ffmpeg.zip",
                "ffmpeg.exe",
                "ffprobe.exe",
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
                ("bin/ffprobe.exe", "ffprobe.exe"),
                lambda: tmpdir,
                fake_download,
                fake_install,
                lambda: {},
                lambda versions: True,
                lambda downloaded, total: progress.append((downloaded, total)),
                expected_digest="sha256:" + hashlib.sha256(b"zip").hexdigest(),
            )

            self.assertTrue(result)
            self.assertEqual((Path(tmpdir) / "ffmpeg.exe").read_text(encoding="utf-8"), "ffmpeg")
            self.assertEqual((Path(tmpdir) / "ffprobe.exe").read_text(encoding="utf-8"), "ffprobe")
            self.assertFalse(Path(install_calls[0][0]).exists())

        self.assertEqual(progress, [(10, 100)])
        self.assertEqual(install_calls[0][3], "2026.07.01")

    def test_download_and_install_ffmpeg_zip_returns_false_without_url(self):
        result = download_and_install_ffmpeg_zip(
            "2026.07.01",
            None,
            "ffmpeg.exe",
            "ffprobe.exe",
            ("ffmpeg.exe",),
            ("ffprobe.exe",),
            lambda: "unused",
            lambda *args: True,
            lambda *args: True,
            lambda: {},
            lambda versions: True,
        )

        self.assertFalse(result)

    def test_download_and_install_ffmpeg_zip_stops_when_cancelled_after_download(self):
        install_calls = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                Path(dest_path).write_bytes(b"zip")
                return True

            result = download_and_install_ffmpeg_zip(
                "2026.07.01",
                "https://example.test/ffmpeg.zip",
                "ffmpeg.exe",
                "ffprobe.exe",
                ("ffmpeg.exe",),
                ("ffprobe.exe",),
                lambda: tmpdir,
                fake_download,
                lambda *args: install_calls.append(args) or True,
                lambda: {},
                lambda versions: True,
                check_cancel=lambda: True,
                expected_digest="sha256:" + hashlib.sha256(b"zip").hexdigest(),
            )

            self.assertFalse(result)

        self.assertEqual(install_calls, [])

    def test_download_and_install_ffmpeg_zip_rejects_digest_mismatch(self):
        install_calls = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                Path(dest_path).write_bytes(b"tampered zip")
                return True

            result = download_and_install_ffmpeg_zip(
                "2026.07.01",
                "https://example.test/ffmpeg.zip",
                "ffmpeg.exe",
                "ffprobe.exe",
                ("ffmpeg.exe",),
                ("ffprobe.exe",),
                lambda: tmpdir,
                fake_download,
                lambda *args: install_calls.append(args) or True,
                lambda: {},
                lambda versions: True,
                expected_digest="sha256:" + "0" * 64,
            )

        self.assertFalse(result)
        self.assertEqual(install_calls, [])


if __name__ == "__main__":
    unittest.main()
