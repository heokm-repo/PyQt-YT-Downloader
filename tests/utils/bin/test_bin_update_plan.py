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

from utils.bin.update_plan import (
    collect_available_updates,
    MANAGED_UPDATE_BINARIES,
    initial_update_results,
    needs_update_from_versions,
    scoped_progress_callback,
    selected_update_binaries,
    update_entry,
)


class BinUpdatePlanTests(unittest.TestCase):
    def test_initial_update_results_defaults_to_managed_binaries(self):
        self.assertEqual(
            initial_update_results(),
            {"yt-dlp": False, "ffmpeg": False, "quickjs": False},
        )
        self.assertEqual(MANAGED_UPDATE_BINARIES, ("yt-dlp", "ffmpeg", "quickjs"))

    def test_initial_update_results_accepts_custom_binary_list(self):
        self.assertEqual(initial_update_results(["a", "b"]), {"a": False, "b": False})

    def test_selected_update_binaries_defaults_when_no_selection(self):
        self.assertEqual(selected_update_binaries(None), ["yt-dlp", "ffmpeg", "quickjs"])

    def test_selected_update_binaries_uses_mapping_keys_in_order(self):
        updates = {"ffmpeg": {"current": "old", "latest": "new"}}

        self.assertEqual(selected_update_binaries(updates), ["ffmpeg"])

    def test_needs_update_from_versions_handles_missing_and_changed_versions(self):
        self.assertTrue(needs_update_from_versions(None, "2.0"))
        self.assertFalse(needs_update_from_versions("1.0", None))
        self.assertFalse(needs_update_from_versions("1.0", "1.0"))
        self.assertTrue(needs_update_from_versions("1.0", "2.0"))

    def test_update_entry_requires_current_and_latest_difference(self):
        self.assertEqual(update_entry("1.0", "2.0"), {"current": "1.0", "latest": "2.0"})
        self.assertIsNone(update_entry("1.0", "1.0"))
        self.assertIsNone(update_entry(None, "2.0"))
        self.assertIsNone(update_entry("1.0", None))

    def test_collect_available_updates_builds_entries_for_changed_versions(self):
        updates = collect_available_updates(
            {"yt-dlp": "1.0", "ffmpeg": "2.0"},
            {"yt-dlp": "1.1", "ffmpeg": "2.0", "quickjs": "3.0"},
        )

        self.assertEqual(updates, {"yt-dlp": {"current": "1.0", "latest": "1.1"}})

    def test_scoped_progress_callback_returns_none_without_callback(self):
        self.assertIsNone(scoped_progress_callback("yt-dlp", None))

    def test_scoped_progress_callback_adds_binary_name(self):
        calls = []
        callback = scoped_progress_callback(
            "ffmpeg",
            lambda name, downloaded, total: calls.append((name, downloaded, total)),
        )

        callback(10, 100)

        self.assertEqual(calls, [("ffmpeg", 10, 100)])


if __name__ == "__main__":
    unittest.main()
