import os
import sys
import unittest
from dataclasses import dataclass, field
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.tasks.task_resume_plan import build_resume_task_plan


@dataclass
class FakeTask:
    url: str = "https://example.invalid/video"
    settings: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=lambda: {"id": "abc123"})
    output_path: str = ""


class TaskResumePlanTests(unittest.TestCase):
    def test_build_resume_task_plan_uses_task_settings_when_present(self):
        task = FakeTask(settings={"format": "webm"})
        plan = build_resume_task_plan(task, {"format": "mp4"})

        self.assertEqual(plan.url, task.url)
        self.assertEqual(plan.settings, {"format": "webm"})
        self.assertEqual(plan.meta, {"id": "abc123"})

    def test_build_resume_task_plan_falls_back_to_default_settings_copy(self):
        defaults = {"format": "mp4"}
        plan = build_resume_task_plan(FakeTask(), defaults)
        defaults["format"] = "mkv"

        self.assertEqual(plan.settings, {"format": "mp4"})

    def test_build_resume_task_plan_passes_saved_output_for_final_file_check(self):
        task = FakeTask(
            settings={"format": "mp4"},
            output_path="C:/Downloads/title.mp4",
        )

        plan = build_resume_task_plan(task, {})

        self.assertEqual(
            plan.settings["_resume_output_path"],
            "C:/Downloads/title.mp4",
        )

    def test_build_resume_task_plan_allows_empty_metadata_for_legacy_resume(self):
        plan = build_resume_task_plan(FakeTask(meta={}), {"format": "mp4"})

        self.assertIsNotNone(plan)
        self.assertEqual(plan.meta, {})

    def test_build_resume_task_plan_returns_none_without_url(self):
        self.assertIsNone(build_resume_task_plan(FakeTask(url=""), {"format": "mp4"}))


if __name__ == "__main__":
    unittest.main()
