import os
import sys
import unittest
from dataclasses import dataclass, field

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import TaskStatus
from data.models import DownloadTask
from gui.main_window.download_toggle import (
    build_download_toggle_plan,
    mark_downloading_tasks_paused,
    pause_downloading_tasks,
    resume_paused_tasks,
)


class FakeLabel:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class FakeWidget:
    def __init__(self):
        self.calls = []
        self.status_label = FakeLabel()

    def set_status(self, status):
        self.calls.append(("set_status", status))

    def set_paused(self):
        self.calls.append(("set_paused", None))


class FakeScheduler:
    def __init__(self, paused_ids=None):
        self.paused_ids = set(paused_ids or [])
        self.resumed = []
        self.added = []

    def is_task_paused(self, task_id):
        return task_id in self.paused_ids

    def resume_task(self, task_id):
        self.resumed.append(task_id)
        self.paused_ids.discard(task_id)

    def add_task(self, priority, task_id, url, settings, metadata, is_resume=False):
        self.added.append((priority, task_id, url, settings, metadata, is_resume))


@dataclass
class FakeTask:
    id: int
    url: str = "url"
    status: TaskStatus = TaskStatus.WAITING
    settings: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


class DownloadToggleTests(unittest.TestCase):
    def test_build_download_toggle_plan_disables_currently_enabled_downloads(self):
        plan = build_download_toggle_plan(True, "Enabled", "Paused")

        self.assertFalse(plan.enabled)
        self.assertEqual(plan.status_text, "Paused")

    def test_build_download_toggle_plan_enables_currently_paused_downloads(self):
        plan = build_download_toggle_plan(False, "Enabled", "Paused")

        self.assertTrue(plan.enabled)
        self.assertEqual(plan.status_text, "Enabled")

    def test_resume_paused_tasks_requeues_and_updates_widget(self):
        task = FakeTask(10, status=TaskStatus.PAUSED, settings={"format": "mp4"}, meta={"title": "Video"})
        widget = FakeWidget()
        scheduler = FakeScheduler(paused_ids=[10])

        resume_paused_tasks([task], {10: widget}, scheduler, {"format": "webm"}, "Waiting...")

        self.assertEqual(task.status, TaskStatus.WAITING)
        self.assertEqual(scheduler.resumed, [10])
        self.assertEqual(widget.calls, [("set_status", "waiting")])
        self.assertEqual(widget.status_label.text, "Waiting...")
        self.assertEqual(scheduler.added, [(1, 10, "url", {"format": "mp4"}, {"title": "Video"}, True)])

    def test_resume_paused_tasks_uses_default_settings_when_task_settings_empty(self):
        task = FakeTask(10, status=TaskStatus.PAUSED)
        scheduler = FakeScheduler()

        resume_paused_tasks([task], {}, scheduler, {"format": "webm"}, "Waiting...")

        self.assertEqual(scheduler.added[0][3], {"format": "webm"})
        self.assertEqual(scheduler.added[0][4], {})

    def test_pause_downloading_tasks_marks_only_downloading_tasks(self):
        downloading = FakeTask(10, status=TaskStatus.DOWNLOADING)
        waiting = FakeTask(20, status=TaskStatus.WAITING)
        widget = FakeWidget()

        pause_downloading_tasks([downloading, waiting], {10: widget})

        self.assertEqual(downloading.status, TaskStatus.PAUSED)
        self.assertEqual(waiting.status, TaskStatus.WAITING)
        self.assertEqual(widget.calls, [("set_paused", None)])

    def test_global_pause_resume_requeues_same_persisted_workspace_uuid(self):
        task = DownloadTask(
            id=30,
            url="https://media.example/Watch/ABC",
            status=TaskStatus.DOWNLOADING,
            video_id="CaseSensitive-ID",
            extractor="Example",
            settings={"format": "mp4"},
            meta={"title": "Video"},
            legacy_workspace=True,
        )
        original_workspace_id = task.workspace_id
        scheduler = FakeScheduler(paused_ids=[30])

        pause_downloading_tasks([task], {})
        resume_paused_tasks(
            [task],
            {},
            scheduler,
            {"format": "webm"},
            "Waiting...",
        )

        queued_settings = scheduler.added[0][3]
        self.assertEqual(task.workspace_id, original_workspace_id)
        self.assertEqual(
            queued_settings["_workspace_id"],
            original_workspace_id,
        )
        self.assertEqual(
            queued_settings["_legacy_workspace_identity"],
            {
                "extractor": "Example",
                "video_id": "CaseSensitive-ID",
                "url": "https://media.example/Watch/ABC",
                "format": "mp4",
            },
        )
        self.assertNotIn("_workspace_id", task.settings)

    def test_mark_downloading_tasks_paused_returns_changed_ids(self):
        downloading = FakeTask(10, status=TaskStatus.DOWNLOADING)
        failed = FakeTask(20, status=TaskStatus.FAILED)

        changed_ids = mark_downloading_tasks_paused([downloading, failed])

        self.assertEqual(changed_ids, [10])
        self.assertEqual(downloading.status, TaskStatus.PAUSED)
        self.assertEqual(failed.status, TaskStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
