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

from gui.tasks.task_widget_registry import (
    apply_task_title_override,
    create_registered_task_widget,
    register_task_widget,
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


class TaskWidgetRegistryTests(unittest.TestCase):
    def test_apply_task_title_override_uses_uppercase_format(self):
        widget = FakeWidget()

        apply_task_title_override(widget, {"format": "webm"}, "Video ID: abc")

        self.assertEqual(widget.title_label.text, "[WEBM] Video ID: abc")

    def test_apply_task_title_override_noops_without_title(self):
        widget = FakeWidget()

        apply_task_title_override(widget, {"format": "webm"}, None)

        self.assertIsNone(widget.title_label.text)

    def test_register_task_widget_connects_inserts_and_records_widget(self):
        widget = FakeWidget()
        layout = FakeLayout()
        widgets = {}
        connected = []

        register_task_widget(widget, 10, layout, widgets, connected.append)

        self.assertEqual(connected, [widget])
        self.assertEqual(layout.inserted, [(0, widget)])
        self.assertIs(widgets[10], widget)

    def test_create_registered_task_widget_creates_overrides_and_registers(self):
        created_args = []
        layout = FakeLayout()
        widgets = {}
        connected = []
        parent = object()
        settings = {"format": "mp4"}

        def widget_factory(task_id, url, widget_settings, widget_parent):
            created_args.append((task_id, url, widget_settings, widget_parent))
            return FakeWidget()

        widget = create_registered_task_widget(
            22,
            "https://example.test/22",
            settings,
            "Video ID: 22",
            parent,
            layout,
            widgets,
            connected.append,
            widget_factory,
        )

        self.assertEqual(
            created_args,
            [(22, "https://example.test/22", settings, parent)],
        )
        self.assertEqual(widget.title_label.text, "[MP4] Video ID: 22")
        self.assertEqual(connected, [widget])
        self.assertEqual(layout.inserted, [(0, widget)])
        self.assertIs(widgets[22], widget)


if __name__ == "__main__":
    unittest.main()