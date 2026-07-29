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

from PyQt5.QtWidgets import QApplication

from locales.strings import STR
from utils.settings_store import default_settings
from gui.windows.settings_dialog import SettingsDialog


class SettingsDialogCompatibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_compatibility_labels_are_strings(self):
        self.assertIsInstance(STR.SETTINGS_CHK_COMPATIBILITY, str)
        self.assertIsInstance(STR.TOOLTIP_COMPATIBILITY, str)
        self.assertIsInstance(STR.BTN_RESTART_NOW, str)
        self.assertIsInstance(STR.MSG_UPDATE_ALL_LATEST, str)

    def test_settings_dialog_builds_with_compatibility_option(self):
        dialog = SettingsDialog(default_settings())
        self.addCleanup(dialog.close)

        self.assertFalse(dialog.compatibility_check.isChecked())


if __name__ == "__main__":
    unittest.main()
