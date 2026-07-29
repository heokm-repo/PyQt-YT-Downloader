import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtWidgets import QApplication

from constants import APP_VERSION
from gui.windows.settings_dialog import SettingsDialog
from locales.strings import STR
from utils.settings_store import default_settings


class FakeSignal:
    def __init__(self):
        self._slots = []

    def connect(self, slot):
        self._slots.append(slot)

    def disconnect(self, slot):
        try:
            self._slots.remove(slot)
        except ValueError as exc:
            raise TypeError("slot is not connected") from exc

    def emit(self, *args):
        for slot in tuple(self._slots):
            slot(*args)


class FakeUpdateWorker:
    instances = []

    def __init__(self, current_app_version, parent=None):
        self.current_app_version = current_app_version
        self.parent = parent
        self.completed = FakeSignal()
        self.failed = FakeSignal()
        self.finished = FakeSignal()
        self.started = False
        self.deleted = False
        type(self).instances.append(self)

    def start(self):
        self.started = True

    def isRunning(self):
        return self.started

    def deleteLater(self):
        self.deleted = True


class SettingsDialogUpdateWorkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        FakeUpdateWorker.instances = []

    def test_click_starts_worker_and_returns_with_busy_state(self):
        dialog = SettingsDialog(
            default_settings(),
            update_worker_factory=FakeUpdateWorker,
        )
        self.addCleanup(dialog.close)

        dialog._on_check_update_clicked()

        worker = FakeUpdateWorker.instances[0]
        self.assertTrue(worker.started)
        self.assertEqual(worker.current_app_version, APP_VERSION)
        self.assertFalse(dialog.update_check_button.isEnabled())
        self.assertEqual(dialog.update_check_button.text(), STR.MSG_CHECKING_INFO)

    def test_worker_failure_is_visible_and_restores_button(self):
        dialog = SettingsDialog(
            default_settings(),
            update_worker_factory=FakeUpdateWorker,
        )
        self.addCleanup(dialog.close)
        dialog._on_check_update_clicked()
        worker = FakeUpdateWorker.instances[0]

        with patch(
            "gui.windows.settings_dialog.show_error",
        ) as show_error:
            worker.failed.emit("network unavailable")

        self.assertTrue(dialog.update_check_button.isEnabled())
        self.assertEqual(
            dialog.update_check_button.text(),
            STR.SETTINGS_BTN_CHECK_UPDATE,
        )
        show_error.assert_called_once()
        self.assertIn("network unavailable", show_error.call_args.args[2])

    def test_closing_dialog_keeps_app_owned_worker_cleanup_connected(self):
        dialog = SettingsDialog(
            default_settings(),
            update_worker_factory=FakeUpdateWorker,
        )
        dialog._on_check_update_clicked()
        worker = FakeUpdateWorker.instances[0]

        self.assertIs(worker.parent, self.app)
        dialog.reject()
        worker.completed.emit(object())
        worker.failed.emit("must not reopen UI")
        worker.finished.emit()

        self.assertIsNone(dialog._update_check_worker)
        self.assertTrue(worker.deleted)
        self.assertTrue(dialog.update_check_button.isEnabled())


if __name__ == "__main__":
    unittest.main()
