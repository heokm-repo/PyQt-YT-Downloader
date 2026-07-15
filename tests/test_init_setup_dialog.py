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

from PyQt5.QtWidgets import QApplication

from gui.dialogs.init_setup_dialog import InitSetupDialog


class InitSetupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_first_launch_dialog_uses_available_icon(self):
        dialog = InitSetupDialog()

        self.assertIsNotNone(dialog.icon_label)
        self.assertIsNotNone(dialog.icon_label.pixmap())
        self.assertFalse(dialog.icon_label.pixmap().isNull())


if __name__ == "__main__":
    unittest.main()
