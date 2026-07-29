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

from constants import KEY_LANGUAGE
from gui.dialogs import init_setup_dialog
from gui.dialogs.init_setup_dialog import InitSetupDialog


class InitSetupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_first_launch_dialog_uses_available_icon(self):
        dialog = InitSetupDialog()
        self.addCleanup(dialog.close)

        self.assertIsNotNone(dialog.icon_label)
        self.assertIsNotNone(dialog.icon_label.pixmap())
        self.assertFalse(dialog.icon_label.pixmap().isNull())

    def test_repair_setup_keeps_saved_language(self):
        saved_settings = {KEY_LANGUAGE: "ko"}

        with patch.object(
            init_setup_dialog,
            "load_settings",
            return_value=saved_settings.copy(),
        ), patch.object(
            init_setup_dialog,
            "save_settings",
        ) as save_settings, patch.object(
            init_setup_dialog,
            "set_language",
        ) as set_language:
            dialog = InitSetupDialog()
            self.addCleanup(dialog.close)

            self.assertEqual(dialog.current_lang, "ko")
            self.assertEqual(dialog.lang_combo.currentData(), "ko")
            dialog._on_start_clicked()

        set_language.assert_called_with("ko")
        self.assertEqual(save_settings.call_args.args[0][KEY_LANGUAGE], "ko")


if __name__ == "__main__":
    unittest.main()
