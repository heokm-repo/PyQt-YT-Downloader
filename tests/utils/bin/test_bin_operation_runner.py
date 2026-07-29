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

from utils.bin.operation_runner import download_initial_binary, run_binary_updates, run_initial_binary_downloads, update_binary_if_needed


class BinOperationRunnerTests(unittest.TestCase):
    def test_download_initial_binary_scopes_progress_callback(self):
        progress = []

        def downloader(progress_callback=None, check_cancel=None):
            progress_callback(50, 100)
            return True

        result = download_initial_binary(
            "yt-dlp",
            downloader,
            lambda name, downloaded, total: progress.append((name, downloaded, total)),
            None,
            "failed",
        )

        self.assertTrue(result)
        self.assertEqual(progress, [("yt-dlp", 50, 100)])

    def test_download_initial_binary_failure_returns_false(self):
        result = download_initial_binary("ffmpeg", lambda *_: False, None, None, "failed")

        self.assertFalse(result)

    def test_run_initial_binary_downloads_runs_specs_in_order(self):
        calls = []

        def downloader_for(name):
            def downloader(progress_callback=None, check_cancel=None):
                calls.append(name)
                return True

            return downloader

        result = run_initial_binary_downloads(
            (
                ("yt-dlp", downloader_for("yt-dlp"), "failed yt-dlp"),
                ("ffmpeg", downloader_for("ffmpeg"), "failed ffmpeg"),
                ("quickjs", downloader_for("quickjs"), "failed quickjs"),
            ),
            None,
            None,
        )

        self.assertTrue(result)
        self.assertEqual(calls, ["yt-dlp", "ffmpeg", "quickjs"])

    def test_run_initial_binary_downloads_stops_on_failure(self):
        calls = []

        def passing(progress_callback=None, check_cancel=None):
            calls.append("yt-dlp")
            return True

        def failing(progress_callback=None, check_cancel=None):
            calls.append("ffmpeg")
            return False

        result = run_initial_binary_downloads(
            (
                ("yt-dlp", passing, "failed yt-dlp"),
                ("ffmpeg", failing, "failed ffmpeg"),
                ("quickjs", passing, "failed quickjs"),
            ),
            None,
            None,
        )

        self.assertFalse(result)
        self.assertEqual(calls, ["yt-dlp", "ffmpeg"])

    def test_run_binary_updates_updates_only_selected_binary(self):
        downloads = []

        def downloader_for(name):
            def downloader(progress_callback=None, check_cancel=None):
                downloads.append(name)
                return True

            return downloader

        result = run_binary_updates(
            (
                ("yt-dlp", downloader_for("yt-dlp")),
                ("ffmpeg", downloader_for("ffmpeg")),
            ),
            {"yt-dlp": False, "ffmpeg": False},
            {"ffmpeg": {"current": "old", "latest": "new"}},
            lambda name: True,
            None,
            None,
        )

        self.assertEqual(result, {"yt-dlp": True, "ffmpeg": True})
        self.assertEqual(downloads, ["ffmpeg"])

    def test_run_binary_updates_stops_after_cancel_between_binaries(self):
        cancel_results = iter([False, True])
        downloads = []

        result = run_binary_updates(
            (
                ("yt-dlp", lambda *_: downloads.append("yt-dlp") or True),
                ("ffmpeg", lambda *_: downloads.append("ffmpeg") or True),
            ),
            {"yt-dlp": False, "ffmpeg": False},
            None,
            lambda name: True,
            None,
            lambda: next(cancel_results),
        )

        self.assertEqual(result, {"yt-dlp": True, "ffmpeg": False})
        self.assertEqual(downloads, ["yt-dlp"])

    def test_update_binary_if_needed_skips_unselected_binary(self):
        result = update_binary_if_needed(
            "yt-dlp",
            lambda *_: False,
            ["ffmpeg"],
            lambda name: True,
            None,
            None,
        )

        self.assertTrue(result)

    def test_update_binary_if_needed_downloads_selected_stale_binary(self):
        calls = []
        progress = []

        def downloader(progress_callback=None, check_cancel=None):
            calls.append("download")
            progress_callback(10, 20)
            return True

        result = update_binary_if_needed(
            "ffmpeg",
            downloader,
            ["ffmpeg"],
            lambda name: True,
            lambda name, downloaded, total: progress.append((name, downloaded, total)),
            None,
        )

        self.assertTrue(result)
        self.assertEqual(calls, ["download"])
        self.assertEqual(progress, [("ffmpeg", 10, 20)])


if __name__ == "__main__":
    unittest.main()
