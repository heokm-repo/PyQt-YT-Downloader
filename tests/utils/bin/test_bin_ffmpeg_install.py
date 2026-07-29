import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin import ffmpeg_install
from utils.bin.ffmpeg_install import install_ffmpeg_from_zip


class BinFfmpegInstallTests(unittest.TestCase):
    def test_install_ffmpeg_from_zip_extracts_binary_and_saves_version(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            final_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"binary")
                archive.writestr("build/bin/ffprobe.exe", b"probe")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(final_path),
                str(ffprobe_path),
                "2026.07.01",
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
                ("bin/ffprobe.exe", "ffprobe.exe"),
                lambda: {"yt-dlp": "2026"},
                lambda versions: saved.append(versions) or True,
            )

            self.assertTrue(result)
            self.assertEqual(final_path.read_bytes(), b"binary")
            self.assertEqual(ffprobe_path.read_bytes(), b"probe")

        self.assertEqual(saved[0]["ffmpeg"], "2026.07.01")
        self.assertNotIn("last_check", saved[0])

    def test_install_ffmpeg_from_zip_returns_false_without_matching_member(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            final_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("docs/readme.txt", "ignored")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(final_path),
                str(ffprobe_path),
                "2026.07.01",
                ("bin/ffmpeg.exe", "ffmpeg.exe"),
                ("bin/ffprobe.exe", "ffprobe.exe"),
                lambda: {},
                lambda versions: saved.append(versions) or True,
            )

            self.assertFalse(result)
            self.assertFalse(final_path.exists())
            self.assertFalse(ffprobe_path.exists())
            self.assertEqual(saved, [])

    def test_install_requires_ffprobe_before_saving_version(self):
        saved = []
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            ffmpeg_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"binary")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(ffmpeg_path),
                str(ffprobe_path),
                "2026.07.01",
                ("bin/ffmpeg.exe",),
                ("bin/ffprobe.exe",),
                lambda: {},
                lambda versions: saved.append(versions) or True,
            )

        self.assertFalse(result)
        self.assertEqual(saved, [])

    def test_second_binary_replace_failure_restores_existing_pair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            ffmpeg_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            ffmpeg_path.write_bytes(b"old ffmpeg")
            ffprobe_path.write_bytes(b"old ffprobe")
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"new ffmpeg")
                archive.writestr("build/bin/ffprobe.exe", b"new ffprobe")

            real_replace = os.replace

            def replace_with_second_install_failure(source, target):
                if (
                    target == str(ffprobe_path)
                    and str(source).endswith(".installing")
                ):
                    raise OSError("simulated ffprobe commit failure")
                return real_replace(source, target)

            with patch.object(
                ffmpeg_install.os,
                "replace",
                side_effect=replace_with_second_install_failure,
            ):
                result = install_ffmpeg_from_zip(
                    str(zip_path),
                    str(ffmpeg_path),
                    str(ffprobe_path),
                    "2026.07.01",
                    ("bin/ffmpeg.exe",),
                    ("bin/ffprobe.exe",),
                    lambda: {"ffmpeg": "old"},
                    lambda _versions: True,
                )

            self.assertFalse(result)
            self.assertEqual(ffmpeg_path.read_bytes(), b"old ffmpeg")
            self.assertEqual(ffprobe_path.read_bytes(), b"old ffprobe")
            self.assertEqual(list(Path(tmpdir).glob("*.backup")), [])
            self.assertEqual(list(Path(tmpdir).glob("*.installing")), [])

    def test_version_save_failure_restores_existing_pair(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            ffmpeg_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            ffmpeg_path.write_bytes(b"old ffmpeg")
            ffprobe_path.write_bytes(b"old ffprobe")
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"new ffmpeg")
                archive.writestr("build/bin/ffprobe.exe", b"new ffprobe")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(ffmpeg_path),
                str(ffprobe_path),
                "2026.07.01",
                ("bin/ffmpeg.exe",),
                ("bin/ffprobe.exe",),
                lambda: {"ffmpeg": "old"},
                lambda _versions: False,
            )

            self.assertFalse(result)
            self.assertEqual(ffmpeg_path.read_bytes(), b"old ffmpeg")
            self.assertEqual(ffprobe_path.read_bytes(), b"old ffprobe")
            self.assertEqual(list(Path(tmpdir).glob("*.backup")), [])
            self.assertEqual(list(Path(tmpdir).glob("*.installing")), [])

    def test_version_save_failure_restores_metadata_snapshot(self):
        stored_versions = {"ffmpeg": "old", "yt-dlp": "existing"}
        save_attempts = []

        def save_versions(versions):
            save_attempts.append(dict(versions))
            stored_versions.clear()
            stored_versions.update(versions)
            return len(save_attempts) > 1

        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = Path(tmpdir) / "ffmpeg.zip"
            ffmpeg_path = Path(tmpdir) / "ffmpeg.exe"
            ffprobe_path = Path(tmpdir) / "ffprobe.exe"
            ffmpeg_path.write_bytes(b"old ffmpeg")
            ffprobe_path.write_bytes(b"old ffprobe")
            with zipfile.ZipFile(zip_path, "w") as archive:
                archive.writestr("build/bin/ffmpeg.exe", b"new ffmpeg")
                archive.writestr("build/bin/ffprobe.exe", b"new ffprobe")

            result = install_ffmpeg_from_zip(
                str(zip_path),
                str(ffmpeg_path),
                str(ffprobe_path),
                "2026.07.01",
                ("bin/ffmpeg.exe",),
                ("bin/ffprobe.exe",),
                lambda: stored_versions,
                save_versions,
            )

            self.assertFalse(result)
            self.assertEqual(ffmpeg_path.read_bytes(), b"old ffmpeg")
            self.assertEqual(ffprobe_path.read_bytes(), b"old ffprobe")

        self.assertEqual(save_attempts[0]["ffmpeg"], "2026.07.01")
        self.assertEqual(
            save_attempts[1],
            {"ffmpeg": "old", "yt-dlp": "existing"},
        )
        self.assertEqual(
            stored_versions,
            {"ffmpeg": "old", "yt-dlp": "existing"},
        )


if __name__ == "__main__":
    unittest.main()
