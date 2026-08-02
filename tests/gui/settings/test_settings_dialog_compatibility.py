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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QPushButton,
    QToolButton,
)

import locales
from locales.strings import STR
from resources.styles import SETTINGS_DIALOG_HEIGHT, SETTINGS_DIALOG_WIDTH
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

    def test_settings_dialog_has_fixed_size_and_opens_centered(self):
        dialog = SettingsDialog(default_settings())
        self.addCleanup(dialog.close)

        self.assertFalse(dialog._resizable)
        self.assertIsNone(dialog.maximize_btn)
        self.assertEqual(dialog.width(), SETTINGS_DIALOG_WIDTH)
        self.assertEqual(dialog.height(), SETTINGS_DIALOG_HEIGHT)
        self.assertEqual(dialog.minimumWidth(), SETTINGS_DIALOG_WIDTH)
        self.assertEqual(dialog.minimumHeight(), SETTINGS_DIALOG_HEIGHT)
        self.assertEqual(dialog.maximumWidth(), SETTINGS_DIALOG_WIDTH)
        self.assertEqual(dialog.maximumHeight(), SETTINGS_DIALOG_HEIGHT)
        self.assertEqual(
            dialog.frameGeometry().center(),
            self.app.primaryScreen().availableGeometry().center(),
        )

    def test_tab_content_expands_to_the_action_buttons(self):
        dialog = SettingsDialog(default_settings())
        dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
        self.addCleanup(dialog.close)
        dialog.show()
        self.app.processEvents()

        save_button = dialog.button_layout.itemAt(
            dialog.button_layout.count() - 1
        ).widget()
        gap = save_button.mapTo(dialog, save_button.rect().topLeft()).y() - (
            dialog.tab_widget.mapTo(dialog, dialog.tab_widget.rect().bottomLeft()).y()
        )
        self.assertLessEqual(gap, dialog.container_layout.spacing() + 1)

    def test_settings_controls_are_not_clipped_in_supported_languages(self):
        original_language = locales.get_language()
        self.addCleanup(locales.set_language, original_language)

        text_widget_types = (QLabel, QPushButton, QToolButton, QCheckBox)
        for language_code in locales.SUPPORTED_LANGUAGES:
            with self.subTest(language=language_code):
                locales.set_language(language_code)
                dialog = SettingsDialog(default_settings())
                dialog.setAttribute(Qt.WA_DontShowOnScreen, True)
                dialog.resize(SETTINGS_DIALOG_WIDTH, SETTINGS_DIALOG_HEIGHT)
                dialog.show()
                self.app.processEvents()

                for tab_index in range(dialog.tab_widget.count()):
                    dialog.tab_widget.setCurrentIndex(tab_index)
                    self.app.processEvents()
                    for widget in dialog.findChildren(text_widget_types):
                        if not widget.isVisible() or not widget.text():
                            continue
                        text_width = widget.fontMetrics().horizontalAdvance(widget.text())
                        self.assertLessEqual(
                            text_width,
                            widget.contentsRect().width(),
                            f"{language_code}: {widget.text()}",
                        )

                dialog.close()


if __name__ == "__main__":
    unittest.main()
