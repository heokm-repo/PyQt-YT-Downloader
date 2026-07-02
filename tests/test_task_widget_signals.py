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

from gui.tasks.task_widget_signals import connect_task_widget_signals


class FakeSignal:
    def __init__(self):
        self.connected = []

    def connect(self, callback):
        self.connected.append(callback)


class FakeTaskWidget:
    def __init__(self):
        self.remove_requested = FakeSignal()
        self.pause_requested = FakeSignal()
        self.resume_requested = FakeSignal()
        self.retry_requested = FakeSignal()
        self.play_requested = FakeSignal()
        self.open_folder_requested = FakeSignal()
        self.delete_file_requested = FakeSignal()
        self.clicked = FakeSignal()
        self.right_clicked = FakeSignal()


class FakeWindow:
    def __init__(self):
        self.calls = []

    def remove_task_from_list(self, task_id): self.calls.append(("remove", task_id))
    def pause_task(self, task_id): self.calls.append(("pause", task_id))
    def resume_task(self, task_id): self.calls.append(("resume", task_id))
    def retry_task(self, task_id): self.calls.append(("retry", task_id))
    def play_file(self, task_id): self.calls.append(("play", task_id))
    def open_folder(self, task_id): self.calls.append(("open_folder", task_id))
    def delete_file(self, task_id, confirm=True): self.calls.append(("delete_file", task_id, confirm))
    def on_task_clicked(self, task_id, modifiers): self.calls.append(("clicked", task_id, modifiers))
    def show_context_menu(self, task_id, pos): self.calls.append(("context", task_id, pos))


class TaskWidgetSignalsTests(unittest.TestCase):
    def test_connect_task_widget_signals_wires_main_handlers(self):
        widget = FakeTaskWidget()
        window = FakeWindow()

        connect_task_widget_signals(widget, window)

        widget.pause_requested.connected[0](10)
        widget.resume_requested.connected[0](11)
        widget.clicked.connected[0](12, "ctrl")
        widget.right_clicked.connected[0](13, "pos")

        self.assertEqual(
            window.calls,
            [("pause", 10), ("resume", 11), ("clicked", 12, "ctrl"), ("context", 13, "pos")],
        )

    def test_delete_signal_forces_confirmation(self):
        widget = FakeTaskWidget()
        window = FakeWindow()

        connect_task_widget_signals(widget, window)
        widget.delete_file_requested.connected[0](10)

        self.assertEqual(window.calls, [("delete_file", 10, True)])


if __name__ == "__main__":
    unittest.main()
