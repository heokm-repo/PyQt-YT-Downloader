import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.tasks.playlist_registration import build_playlist_registration_decision


class PlaylistRegistrationTests(unittest.TestCase):
    def test_decision_without_duplicates_uses_filtered_ids_and_skips_confirmation(self):
        calls = []

        def ask_exclude_duplicates(_total_count, _duplicate_count):
            calls.append((_total_count, _duplicate_count))
            return False

        decision = build_playlist_registration_decision(
            ["a", "b"],
            ["a", "b"],
            duplicate_count=0,
            ask_exclude_duplicates=ask_exclude_duplicates,
        )

        self.assertEqual(decision.video_ids, ["a", "b"])
        self.assertEqual(decision.duplicate_count, 0)
        self.assertTrue(decision.exclude_duplicates)
        self.assertTrue(decision.has_videos)
        self.assertEqual(calls, [])

    def test_decision_excludes_duplicates_when_user_accepts_default(self):
        calls = []

        def ask_exclude_duplicates(total_count, duplicate_count):
            calls.append((total_count, duplicate_count))
            return True

        decision = build_playlist_registration_decision(
            ["a", "b", "c"],
            ["a", "c"],
            duplicate_count=1,
            ask_exclude_duplicates=ask_exclude_duplicates,
        )

        self.assertEqual(decision.video_ids, ["a", "c"])
        self.assertTrue(decision.exclude_duplicates)
        self.assertEqual(calls, [(3, 1)])

    def test_decision_keeps_all_ids_when_user_rejects_excluding_duplicates(self):
        decision = build_playlist_registration_decision(
            ["a", "b", "c"],
            ["a", "c"],
            duplicate_count=1,
            ask_exclude_duplicates=lambda _total, _duplicates: False,
        )

        self.assertEqual(decision.video_ids, ["a", "b", "c"])
        self.assertFalse(decision.exclude_duplicates)

    def test_decision_reports_no_videos_when_filtered_ids_are_empty(self):
        decision = build_playlist_registration_decision(
            ["a"],
            [],
            duplicate_count=1,
            ask_exclude_duplicates=lambda _total, _duplicates: True,
        )

        self.assertEqual(decision.video_ids, [])
        self.assertFalse(decision.has_videos)


if __name__ == "__main__":
    unittest.main()
