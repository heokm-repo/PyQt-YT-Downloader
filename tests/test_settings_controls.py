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

from constants import MAX_DOWNLOADS_RANGE
from gui.settings.settings_controls import (
    create_format_combo,
    create_language_combo,
    create_max_downloads_spin,
    create_settings_combo,
    create_version_row,
)


class SettingsControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_create_settings_combo_sets_current_value(self):
        combo = create_settings_combo(["720p", "1080p"], "1080p")

        self.assertEqual(combo.currentText(), "1080p")

    def test_create_language_combo_selects_language_code(self):
        combo = create_language_combo("en")

        self.assertTrue(combo.currentText().startswith("en - "))

    def test_create_format_combo_adds_disabled_headers_and_selects_format(self):
        combo = create_format_combo("mp3", "Video", "Audio")
        model = combo.model()

        self.assertEqual(combo.currentText(), "mp3")
        self.assertEqual(combo.itemText(0), "Video")
        self.assertFalse(model.item(0).isEnabled())

    def test_create_max_downloads_spin_sets_range_and_value(self):
        spinbox = create_max_downloads_spin(3)

        self.assertEqual(spinbox.value(), 3)
        self.assertEqual(spinbox.minimum(), MAX_DOWNLOADS_RANGE[0])
        self.assertEqual(spinbox.maximum(), MAX_DOWNLOADS_RANGE[1])

    def test_create_version_row_contains_label_and_value(self):
        row = create_version_row("Version", "1.2.3")

        self.assertEqual(row.itemAt(0).widget().text(), "Version")
        self.assertEqual(row.itemAt(1).widget().text(), "1.2.3")


if __name__ == "__main__":
    unittest.main()
