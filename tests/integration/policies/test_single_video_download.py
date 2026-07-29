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

from gui.tasks.duplicate_check_target import DuplicateCheckTarget
from gui.tasks.single_video_download import (
    build_single_video_download_plan,
    review_single_video_duplicate,
    single_video_duplicate_cancelled,
)


class FakeDuplicateChecker:
    def __init__(self, is_duplicate, duplicate_task=None):
        self.return_is_duplicate = is_duplicate
        self.duplicate_task = duplicate_task
        self.calls = []

    def is_duplicate(self, extractor, video_id, task_id, tasks, target_format):
        self.calls.append(
            {
                "extractor": extractor,
                "video_id": video_id,
                "task_id": task_id,
                "tasks": tasks,
                "target_format": target_format,
            }
        )
        return (
            self.return_is_duplicate,
            "Duplicate message",
            self.duplicate_task,
        )


class SingleVideoDownloadTests(unittest.TestCase):
    def test_build_single_video_download_plan_copies_settings_and_builds_target(self):
        settings = {"format": "webm"}

        plan = build_single_video_download_plan(
            "https://example.test/watch",
            "abc123",
            "youtube",
            settings,
        )

        self.assertEqual(plan.clean_url, "https://example.test/watch")
        self.assertEqual(plan.video_id, "abc123")
        self.assertEqual(plan.extractor, "youtube")
        self.assertEqual(plan.settings, {"format": "webm"})
        self.assertIsNot(plan.settings, settings)
        self.assertEqual(plan.duplicate_target.target_format, "webm")

    def test_build_single_video_download_plan_defaults_missing_extractor(self):
        plan = build_single_video_download_plan(
            "https://example.test/watch",
            "abc123",
            None,
            {},
        )

        self.assertEqual(plan.extractor, "unknown")
        self.assertEqual(plan.duplicate_target.extractor, "unknown")

    def test_build_single_video_download_plan_without_video_id_has_no_target(self):
        plan = build_single_video_download_plan(
            "https://example.test/watch",
            None,
            "youtube",
            {},
        )

        self.assertIsNone(plan.duplicate_target)

    def test_single_video_duplicate_cancelled_skips_without_target(self):
        checker = FakeDuplicateChecker(is_duplicate=True)

        self.assertFalse(single_video_duplicate_cancelled(checker, None, ["task"]))
        self.assertEqual(checker.calls, [])

    def test_single_video_duplicate_cancelled_returns_true_when_user_rejects_duplicate(self):
        checker = FakeDuplicateChecker(is_duplicate=True)
        target = DuplicateCheckTarget("youtube", "abc123", "mp4")
        confirmations = []

        self.assertTrue(
            single_video_duplicate_cancelled(
                checker,
                target,
                ["task"],
                lambda message: confirmations.append(message) or False,
            )
        )

        self.assertEqual(confirmations, ["Duplicate message"])
        self.assertEqual(
            checker.calls,
            [
                {
                    "extractor": "youtube",
                    "video_id": "abc123",
                    "task_id": -1,
                    "tasks": ["task"],
                    "target_format": "mp4",
                }
            ],
        )

    def test_single_video_duplicate_cancelled_allows_when_user_accepts_duplicate(self):
        checker = FakeDuplicateChecker(is_duplicate=True)
        target = DuplicateCheckTarget("youtube", "abc123", "mkv")

        self.assertFalse(
            single_video_duplicate_cancelled(
                checker,
                target,
                [],
                lambda _message: True,
            )
        )
        self.assertEqual(checker.calls[0]["target_format"], "mkv")

    def test_single_video_duplicate_cancelled_allows_non_duplicates(self):
        checker = FakeDuplicateChecker(is_duplicate=False)
        target = DuplicateCheckTarget("youtube", "abc123", "mkv")
        confirmations = []

        self.assertFalse(
            single_video_duplicate_cancelled(
                checker,
                target,
                [],
                lambda message: confirmations.append(message) or False,
            )
        )
        self.assertEqual(confirmations, [])
        self.assertEqual(checker.calls[0]["target_format"], "mkv")

    def test_duplicate_review_returns_active_task_after_user_accepts(self):
        duplicate_task = object()
        checker = FakeDuplicateChecker(True, duplicate_task)
        target = DuplicateCheckTarget("Example", "CaseSensitive-ID", "mp4")

        decision = review_single_video_duplicate(
            checker,
            target,
            [],
            lambda _message: True,
        )

        self.assertFalse(decision.cancelled)
        self.assertIs(decision.duplicate_task, duplicate_task)
        self.assertEqual(checker.calls[0]["extractor"], "Example")
        self.assertEqual(
            checker.calls[0]["video_id"],
            "CaseSensitive-ID",
        )


if __name__ == "__main__":
    unittest.main()
