import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin import manager as bin_manager


class BinManagerDownloadsTests(unittest.TestCase):
    def test_download_ytdlp_installs_downloaded_executable(self):
        saved = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                self.assertEqual(url, "https://example.test/yt-dlp.exe")
                Path(dest_path).write_text("downloaded", encoding="utf-8")
                return True

            with patch.object(bin_manager, "get_bin_path", return_value=tmpdir), \
                    patch.object(
                        bin_manager,
                        "check_ytdlp_latest_version",
                        return_value=("2026.07.01", "https://example.test/yt-dlp.exe"),
                    ), \
                    patch.object(bin_manager, "download_file", side_effect=fake_download), \
                    patch.object(bin_manager, "load_versions", return_value={}), \
                    patch.object(bin_manager, "save_versions", side_effect=lambda versions: saved.append(versions) or True):
                self.assertTrue(bin_manager.download_ytdlp())

            final_path = Path(tmpdir) / bin_manager.YTDLP_BINARY
            self.assertEqual(final_path.read_text(encoding="utf-8"), "downloaded")
            self.assertFalse(Path(str(final_path) + ".tmp").exists())

        self.assertEqual(saved[0]["yt-dlp"], "2026.07.01")

    def test_download_quickjs_removes_temp_file_after_failed_download(self):
        saved = []

        with tempfile.TemporaryDirectory() as tmpdir:
            def fake_download(url, dest_path, progress_callback=None, check_cancel=None):
                Path(dest_path).write_text("partial", encoding="utf-8")
                return False

            with patch.object(bin_manager, "get_bin_path", return_value=tmpdir), \
                    patch.object(
                        bin_manager,
                        "check_quickjs_latest_version",
                        return_value=("2026.07.01", "https://example.test/qjs.exe"),
                    ), \
                    patch.object(bin_manager, "download_file", side_effect=fake_download), \
                    patch.object(bin_manager, "save_versions", side_effect=lambda versions: saved.append(versions) or True):
                self.assertFalse(bin_manager.download_quickjs())

            final_path = Path(tmpdir) / bin_manager.QUICKJS_BINARY
            self.assertFalse(final_path.exists())
            self.assertFalse(Path(str(final_path) + ".tmp").exists())

        self.assertEqual(saved, [])

    def test_download_initial_binaries_runs_required_and_optional_downloads(self):
        calls = []
        progress = []

        def downloader_for(binary_name):
            def run(progress_callback=None, check_cancel=None):
                calls.append(binary_name)
                progress_callback(25, 100)
                return True

            return run

        with patch.object(bin_manager, "download_ytdlp", side_effect=downloader_for("yt-dlp")), \
                patch.object(bin_manager, "download_ffmpeg", side_effect=downloader_for("ffmpeg")), \
                patch.object(bin_manager, "download_quickjs", side_effect=downloader_for("quickjs")):
            result = bin_manager.download_initial_binaries(
                lambda name, downloaded, total: progress.append((name, downloaded, total)),
            )

        self.assertTrue(result)
        self.assertEqual(calls, ["yt-dlp", "ffmpeg", "quickjs"])
        self.assertEqual(
            progress,
            [
                ("yt-dlp", 25, 100),
                ("ffmpeg", 25, 100),
                ("quickjs", 25, 100),
            ],
        )

    def test_download_initial_binaries_stops_after_required_failure(self):
        with patch.object(bin_manager, "download_ytdlp", return_value=True) as download_ytdlp, \
                patch.object(bin_manager, "download_ffmpeg", return_value=False) as download_ffmpeg, \
                patch.object(bin_manager, "download_quickjs", return_value=True) as download_quickjs:
            result = bin_manager.download_initial_binaries()

        self.assertFalse(result)
        download_ytdlp.assert_called_once()
        download_ffmpeg.assert_called_once()
        download_quickjs.assert_not_called()

    def test_download_initial_binaries_continues_after_optional_failure(self):
        with patch.object(bin_manager, "download_ytdlp", return_value=True), \
                patch.object(bin_manager, "download_ffmpeg", return_value=True), \
                patch.object(bin_manager, "download_quickjs", return_value=False) as download_quickjs:
            result = bin_manager.download_initial_binaries()

        self.assertTrue(result)
        download_quickjs.assert_called_once()

    def test_update_binaries_updates_only_selected_binary(self):
        saved = []

        with patch.object(bin_manager, "needs_update", return_value=True) as needs_update, \
                patch.object(bin_manager, "download_ytdlp", return_value=True) as download_ytdlp, \
                patch.object(bin_manager, "download_ffmpeg", return_value=True) as download_ffmpeg, \
                patch.object(bin_manager, "load_versions", return_value={}), \
                patch.object(bin_manager, "save_versions", side_effect=lambda versions: saved.append(versions) or True):
            results = bin_manager.update_binaries(
                updates_to_apply={"ffmpeg": {"current": "old", "latest": "new"}},
            )

        self.assertEqual(results, {"yt-dlp": True, "ffmpeg": True})
        needs_update.assert_has_calls([call("ffmpeg")])
        download_ytdlp.assert_not_called()
        download_ffmpeg.assert_called_once()
        self.assertIn("last_check", saved[0])

    def test_update_binaries_stops_after_cancel_between_binaries(self):
        cancel_results = iter([False, True])

        with patch.object(bin_manager, "needs_update", return_value=True) as needs_update, \
                patch.object(bin_manager, "download_ytdlp", return_value=True) as download_ytdlp, \
                patch.object(bin_manager, "download_ffmpeg", return_value=True) as download_ffmpeg, \
                patch.object(bin_manager, "save_versions") as save_versions:
            results = bin_manager.update_binaries(
                check_cancel=lambda: next(cancel_results),
            )

        self.assertEqual(results, {"yt-dlp": True, "ffmpeg": False})
        needs_update.assert_called_once_with("yt-dlp")
        download_ytdlp.assert_called_once()
        download_ffmpeg.assert_not_called()
        save_versions.assert_not_called()


if __name__ == "__main__":
    unittest.main()