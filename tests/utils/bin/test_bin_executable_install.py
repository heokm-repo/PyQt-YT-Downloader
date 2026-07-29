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

from utils.bin.executable_install import download_and_install_executable_binary


class BinExecutableInstallTests(unittest.TestCase):
    def test_download_and_install_executable_binary_installs_and_saves_version(self):
        saved = []
        progress = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                self.assertEqual(url, "https://example.test/tool.exe")
                Path(dest_path).write_text("downloaded", encoding="utf-8")
                progress_callback(10, 100)
                return True

            result = download_and_install_executable_binary(
                "tool",
                "tool.exe",
                "Tool",
                "2026.07.01",
                "https://example.test/tool.exe",
                "missing url",
                lambda: tmpdir,
                fake_download,
                lambda: {},
                lambda versions: saved.append(versions) or True,
                lambda downloaded, total: progress.append((downloaded, total)),
                expected_digest="sha256:" + hashlib.sha256(b"downloaded").hexdigest(),
            )

            final_path = Path(tmpdir) / "tool.exe"
            self.assertTrue(result)
            self.assertEqual(final_path.read_text(encoding="utf-8"), "downloaded")
            self.assertFalse(Path(str(final_path) + ".tmp").exists())

        self.assertEqual(saved[0]["tool"], "2026.07.01")
        self.assertEqual(progress, [(10, 100)])

    def test_download_and_install_executable_binary_removes_temp_after_failed_download(self):
        saved = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                Path(dest_path).write_text("partial", encoding="utf-8")
                return False

            result = download_and_install_executable_binary(
                "tool",
                "tool.exe",
                "Tool",
                "2026.07.01",
                "https://example.test/tool.exe",
                "missing url",
                lambda: tmpdir,
                fake_download,
                lambda: {},
                lambda versions: saved.append(versions) or True,
                expected_digest="sha256:" + hashlib.sha256(b"partial").hexdigest(),
            )

            final_path = Path(tmpdir) / "tool.exe"
            self.assertFalse(result)
            self.assertFalse(final_path.exists())
            self.assertFalse(Path(str(final_path) + ".tmp").exists())

        self.assertEqual(saved, [])

    def test_download_and_install_executable_binary_returns_false_without_url(self):
        result = download_and_install_executable_binary(
            "tool",
            "tool.exe",
            "Tool",
            "2026.07.01",
            None,
            "missing url",
            lambda: "unused",
            lambda *args: True,
            lambda: {},
            lambda versions: True,
        )

        self.assertFalse(result)

    def test_download_and_install_executable_binary_rejects_digest_mismatch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                Path(dest_path).write_bytes(b"tampered")
                return True

            result = download_and_install_executable_binary(
                "tool",
                "tool.exe",
                "Tool",
                "2026.07.01",
                "https://example.test/tool.exe",
                "missing url",
                lambda: tmpdir,
                fake_download,
                lambda: {},
                lambda versions: True,
                expected_digest="sha256:" + "0" * 64,
            )

            self.assertFalse(result)
            self.assertFalse((Path(tmpdir) / "tool.exe").exists())
            self.assertFalse((Path(tmpdir) / "tool.exe.tmp").exists())


if __name__ == "__main__":
    unittest.main()
