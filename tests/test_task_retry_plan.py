import os
import sys
import unittest
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.tasks.duplicate_check_target import DuplicateCheckTarget
from gui.tasks.task_retry_plan import (
    build_retry_task_plan,
    should_continue_retry_after_duplicate_check,
)


@dataclass
class FakeTask:
    url: str
    video_id: Optional[str] = None
    extractor: str = "youtube"


class FakeHistoryManager:
    def __init__(self):
        self.removed = []

    def remove_from_history(self, extractor, video_id, target_format):
        self.removed.append((extractor, video_id, target_format))


def duplicate_checker_factory(is_duplicate, calls):
    class FakeDuplicateChecker:
        def __init__(self, history_manager):
            self.history_manager = history_manager

        def is_duplicate(self, extractor, video_id, task_id, tasks, target_format):
            calls.append(
                {
                    "extractor": extractor,
                    "video_id": video_id,
                    "task_id": task_id,
                    "tasks": tasks,
                    "target_format": target_format,
                    "history_manager": self.history_manager,
                }
            )
            return is_duplicate, "Duplicate message", None

    return FakeDuplicateChecker


class TaskRetryPlanTests(unittest.TestCase):
    def test_build_retry_task_plan_returns_none_without_task_or_url(self):
        self.assertIsNone(build_retry_task_plan(None, {"format": "mp4"}))
        self.assertIsNone(build_retry_task_plan(FakeTask(""), {"format": "mp4"}))

    def test_build_retry_task_plan_includes_url_and_duplicate_target(self):
        plan = build_retry_task_plan(
            FakeTask("https://example.test/watch", "abc123", "youtube"),
            {"format": "webm"},
        )

        self.assertEqual(plan.url, "https://example.test/watch")
        self.assertEqual(plan.duplicate_target.extractor, "youtube")
        self.assertEqual(plan.duplicate_target.video_id, "abc123")
        self.assertEqual(plan.duplicate_target.target_format, "webm")

    def test_build_retry_task_plan_allows_tasks_without_duplicate_target(self):
        plan = build_retry_task_plan(FakeTask("https://example.test/watch"), {})

        self.assertEqual(plan.url, "https://example.test/watch")
        self.assertIsNone(plan.duplicate_target)

    def test_should_continue_retry_without_duplicate_target_skips_checker(self):
        history = FakeHistoryManager()

        def fail_factory(_history):
            raise AssertionError("duplicate checker should not be created")

        self.assertTrue(
            should_continue_retry_after_duplicate_check(
                None,
                1,
                [],
                history,
                object(),
                fail_factory,
            )
        )
        self.assertEqual(history.removed, [])

    def test_should_continue_retry_returns_false_when_user_cancels_duplicate(self):
        history = FakeHistoryManager()
        calls = []
        target = DuplicateCheckTarget("youtube", "abc123", "mp4")
        confirmations = []

        should_continue = should_continue_retry_after_duplicate_check(
            target,
            7,
            ["task"],
            history,
            object(),
            duplicate_checker_factory(True, calls),
            lambda message: confirmations.append(message) or False,
        )

        self.assertFalse(should_continue)
        self.assertEqual(history.removed, [])
        self.assertEqual(confirmations, ["Duplicate message"])
        self.assertEqual(calls[0]["task_id"], 7)
        self.assertEqual(calls[0]["tasks"], ["task"])
        self.assertIs(calls[0]["history_manager"], history)

    def test_should_continue_retry_removes_history_when_user_accepts_duplicate(self):
        history = FakeHistoryManager()
        calls = []
        target = DuplicateCheckTarget("youtube", "abc123", "webm")

        should_continue = should_continue_retry_after_duplicate_check(
            target,
            9,
            [],
            history,
            object(),
            duplicate_checker_factory(True, calls),
            lambda _message: True,
        )

        self.assertTrue(should_continue)
        self.assertEqual(history.removed, [("youtube", "abc123", "webm")])
        self.assertEqual(calls[0]["target_format"], "webm")

    def test_should_continue_retry_removes_history_without_duplicate_prompt(self):
        history = FakeHistoryManager()
        calls = []
        target = DuplicateCheckTarget("youtube", "abc123", "webm")
        confirmations = []

        should_continue = should_continue_retry_after_duplicate_check(
            target,
            9,
            [],
            history,
            object(),
            duplicate_checker_factory(False, calls),
            lambda message: confirmations.append(message) or False,
        )

        self.assertTrue(should_continue)
        self.assertEqual(history.removed, [("youtube", "abc123", "webm")])
        self.assertEqual(confirmations, [])


if __name__ == "__main__":
    unittest.main()