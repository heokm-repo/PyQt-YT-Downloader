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
from gui.tasks.task_widget_restore import create_restored_task_widget, restore_task_widget_state
from locales.strings import STR


class FakeLabel:
    def __init__(self):
        self.text = None

    def setText(self, text):
        self.text = text


class FakeWidget:
    def __init__(self):
        self.calls = []
        self.status_label = FakeLabel()
        self.percent_label = FakeLabel()

    def update_metadata(self, metadata):
        self.calls.append(("update_metadata", metadata))

    def set_finished(self, file_size=None):
        self.calls.append(("set_finished", file_size))

    def set_paused(self):
        self.calls.append(("set_paused", None))

    def set_failed(self, message):
        self.calls.append(("set_failed", message))


class FakeLayout:
    def __init__(self):
        self.inserted = []

    def insertWidget(self, index, widget):
        self.inserted.append((index, widget))


@dataclass
class FakeTask:
    status: TaskStatus
    meta: dict = field(default_factory=dict)
    id: int = 10
    url: str = "https://example.test/video"
    settings: dict = field(default_factory=dict)


class TaskWidgetRestoreTests(unittest.TestCase):
    def test_create_restored_task_widget_creates_registers_and_restores(self):
        created_args = []
        parent = object()
        layout = FakeLayout()
        widgets = {}
        connected = []
        task = FakeTask(
            TaskStatus.FINISHED,
            {"file_size": "2 MB"},
            id=21,
            url="https://example.test/21",
            settings={"format": "mp4"},
        )

        def widget_factory(task_id, url, settings, widget_parent):
            created_args.append((task_id, url, settings, widget_parent))
            return FakeWidget()

        widget = create_restored_task_widget(
            task,
            parent,
            layout,
            widgets,
            connected.append,
            widget_factory,
        )

        self.assertEqual(
            created_args,
            [(21, "https://example.test/21", {"format": "mp4"}, parent)],
        )
        self.assertEqual(layout.inserted, [(0, widget)])
        self.assertEqual(connected, [widget])
        self.assertIs(widgets[21], widget)
        self.assertEqual(
            widget.calls,
            [("update_metadata", task.meta), ("set_finished", "2 MB")],
        )

    def test_finished_task_restores_metadata_and_finished_state(self):
        widget = FakeWidget()
        task = FakeTask(TaskStatus.FINISHED, {"title": "Video", "file_size": "1 MB"})

        restore_task_widget_state(widget, task)

        self.assertEqual(
            widget.calls,
            [("update_metadata", task.meta), ("set_finished", "1 MB")],
        )

    def test_paused_task_restores_labels(self):
        widget = FakeWidget()
        task = FakeTask(TaskStatus.PAUSED)

        restore_task_widget_state(widget, task)

        self.assertEqual(widget.calls, [("set_paused", None)])
        self.assertEqual(widget.status_label.text, STR.STATUS_PAUSED_SAVED)
        self.assertEqual(widget.percent_label.text, STR.STATUS_WAITING_DOTS)

    def test_failed_task_restores_failed_state(self):
        widget = FakeWidget()
        task = FakeTask(TaskStatus.FAILED)

        restore_task_widget_state(widget, task)

        self.assertEqual(widget.calls, [("set_failed", STR.STATUS_IN_PROGRESS)])

    def test_waiting_task_without_metadata_does_not_touch_widget(self):
        widget = FakeWidget()
        task = FakeTask(TaskStatus.WAITING)

        restore_task_widget_state(widget, task)

        self.assertEqual(widget.calls, [])


if __name__ == "__main__":
    unittest.main()