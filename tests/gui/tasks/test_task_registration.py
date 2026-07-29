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

from gui.tasks.task_registration import (
    NORMAL_TASK_PRIORITY,
    build_task_registration_plan,
    register_download_task,
)


class FakeLabel:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class FakeWidget:
    def __init__(self):
        self.title_label = FakeLabel()


class FakeLayout:
    def __init__(self):
        self.inserted = []

    def insertWidget(self, index, widget):
        self.inserted.append((index, widget))


class FakeScheduler:
    def __init__(self):
        self.added = []

    def add_task(self, priority, task_id, url, settings, metadata=None):
        self.added.append((priority, task_id, url, settings, metadata))


class TaskRegistrationTests(unittest.TestCase):
    def test_build_task_registration_plan_copies_settings_and_creates_task(self):
        settings = {"format": "webm", "quality": "best"}

        plan = build_task_registration_plan(
            7,
            "https://example.test/watch",
            settings,
            video_id="abc123",
            extractor="youtube",
            title_override="Video ID: abc123",
        )

        self.assertEqual(plan.task.id, 7)
        self.assertEqual(plan.task.url, "https://example.test/watch")
        self.assertEqual(plan.task.video_id, "abc123")
        self.assertEqual(plan.task.extractor, "youtube")
        self.assertEqual(plan.settings, settings)
        self.assertIs(plan.task.settings, plan.settings)
        self.assertIsNot(plan.settings, settings)
        self.assertEqual(plan.title_override, "Video ID: abc123")
        self.assertEqual(plan.scheduler_priority, NORMAL_TASK_PRIORITY)

    def test_build_task_registration_plan_defaults_optional_metadata(self):
        plan = build_task_registration_plan(3, "https://example.test/watch", {})

        self.assertEqual(plan.task.video_id, None)
        self.assertEqual(plan.task.extractor, "unknown")
        self.assertEqual(plan.settings, {})
        self.assertEqual(plan.title_override, None)

    def test_register_download_task_registers_widget_stores_task_and_enqueues(self):
        created_args = []
        layout = FakeLayout()
        task_widgets = {}
        connected = []
        tasks = []
        scheduler = FakeScheduler()
        parent = object()
        settings = {"format": "mp4"}

        def widget_factory(task_id, url, widget_settings, widget_parent):
            created_args.append((task_id, url, widget_settings, widget_parent))
            return FakeWidget()

        task = register_download_task(
            12,
            "https://example.test/watch?v=12",
            settings,
            parent,
            layout,
            task_widgets,
            connected.append,
            tasks,
            scheduler,
            video_id="12",
            extractor="youtube",
            title_override="Video ID: 12",
            widget_factory=widget_factory,
        )

        widget = task_widgets[12]
        self.assertEqual(task.id, 12)
        self.assertEqual(task.video_id, "12")
        self.assertEqual(task.extractor, "youtube")
        self.assertEqual(tasks, [task])
        self.assertIsNot(task.settings, scheduler.added[0][3])
        self.assertIsNot(task.settings, settings)
        self.assertEqual(
            created_args,
            [(12, "https://example.test/watch?v=12", task.settings, parent)],
        )
        self.assertEqual(widget.title_label.text, "[MP4] Video ID: 12")
        self.assertEqual(connected, [widget])
        self.assertEqual(layout.inserted, [(0, widget)])
        self.assertEqual(
            scheduler.added,
            [(
                NORMAL_TASK_PRIORITY,
                12,
                "https://example.test/watch?v=12",
                {
                    "format": "mp4",
                    "_workspace_id": task.workspace_id,
                },
                {"id": "12", "extractor": "youtube"},
            )],
        )


if __name__ == "__main__":
    unittest.main()
