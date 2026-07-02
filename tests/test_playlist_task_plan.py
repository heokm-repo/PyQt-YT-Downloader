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

from gui.tasks.playlist_task_plan import (
    build_playlist_task_plans,
    select_playlist_registration_ids,
)


class PlaylistTaskPlanTests(unittest.TestCase):
    def test_build_playlist_task_plans_maps_ids_to_urls_and_titles(self):
        plans = build_playlist_task_plans(["abc", "def"], "Video ID: {video_id}")

        self.assertEqual([plan.video_id for plan in plans], ["abc", "def"])
        self.assertEqual(plans[0].url, "https://www.youtube.com/watch?v=abc")
        self.assertEqual(plans[1].title_override, "Video ID: def")
        self.assertEqual(plans[0].extractor, "youtube")

    def test_build_playlist_task_plans_accepts_custom_url_template(self):
        plans = build_playlist_task_plans(
            ["abc"], "Item {video_id}", "https://example.test/{video_id}"
        )

        self.assertEqual(plans[0].url, "https://example.test/abc")
        self.assertEqual(plans[0].title_override, "Item abc")

    def test_select_playlist_registration_ids_excludes_duplicates(self):
        self.assertEqual(
            select_playlist_registration_ids(
                ["a", "b", "c"],
                ["a", "c"],
                duplicate_count=1,
                exclude_duplicates=True,
            ),
            ["a", "c"],
        )

    def test_select_playlist_registration_ids_keeps_all_when_requested(self):
        self.assertEqual(
            select_playlist_registration_ids(
                ["a", "b", "c"],
                ["a", "c"],
                duplicate_count=1,
                exclude_duplicates=False,
            ),
            ["a", "b", "c"],
        )


if __name__ == "__main__":
    unittest.main()
