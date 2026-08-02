import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog

from gui.windows.main_window import YTDownloaderPyQt5


class FakeSignal:
    def __init__(self):
        self.callback = None

    def connect(self, callback):
        self.callback = callback


class FakeSettingsDialog:
    def __init__(self, settings, parent, active_task_check):
        self.settings = settings
        self.parent = parent
        self.active_task_check = active_task_check
        self.finished = FakeSignal()
        self.show_calls = 0
        self.raise_calls = 0
        self.activate_calls = 0
        self.delete_later_calls = 0
        self.window_modality = None
        self.restart_requested = False

    def show(self):
        self.show_calls += 1

    def raise_(self):
        self.raise_calls += 1

    def activateWindow(self):
        self.activate_calls += 1

    def setWindowModality(self, modality):
        self.window_modality = modality

    def deleteLater(self):
        self.delete_later_calls += 1


class SettingsDialogLaunchTests(unittest.TestCase):
    def test_settings_dialog_opens_non_modally(self):
        window = SimpleNamespace(
            _settings_dialog=None,
            settings={"language": "en"},
            tasks=[],
            _handle_settings_dialog_finished=lambda _result: None,
        )

        with patch(
            "gui.windows.main_window.SettingsDialog",
            FakeSettingsDialog,
        ):
            YTDownloaderPyQt5.open_download_options(window)

        dialog = window._settings_dialog
        self.assertIsInstance(dialog, FakeSettingsDialog)
        self.assertIs(dialog.parent, window)
        self.assertEqual(dialog.window_modality, Qt.NonModal)
        self.assertEqual(dialog.show_calls, 1)
        self.assertIsNotNone(dialog.finished.callback)

    def test_existing_settings_dialog_is_raised_instead_of_duplicated(self):
        existing = FakeSettingsDialog({}, None, lambda: False)
        window = SimpleNamespace(_settings_dialog=existing)

        YTDownloaderPyQt5.open_download_options(window)

        self.assertEqual(existing.show_calls, 1)
        self.assertEqual(existing.raise_calls, 1)
        self.assertEqual(existing.activate_calls, 1)

    def test_finished_settings_dialog_is_explicitly_deleted(self):
        dialog = FakeSettingsDialog({}, None, lambda: False)
        window = SimpleNamespace(_settings_dialog=dialog)

        YTDownloaderPyQt5._handle_settings_dialog_finished(
            window,
            QDialog.Rejected,
        )

        self.assertIsNone(window._settings_dialog)
        self.assertEqual(dialog.delete_later_calls, 1)


if __name__ == "__main__":
    unittest.main()
