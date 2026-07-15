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

from PyQt5.QtWidgets import QApplication, QLineEdit, QPushButton, QSizePolicy

from constants import MAX_DOWNLOADS_RANGE
from resources.styles import SETTINGS_BUTTON_WIDTH_PADDING, SETTINGS_INPUT_HEIGHT, TEXT_BUTTON_WIDTH_PADDING
from gui.settings.settings_button_specs import SettingsButtonSpec
from gui.settings.settings_general_rows import create_login_row
from gui.settings.settings_controls import (
    create_format_combo,
    create_language_combo,
    create_max_downloads_spin,
    create_settings_button,
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

    def test_max_downloads_stepper_expands_like_other_form_controls(self):
        stepper = create_max_downloads_spin(3)

        self.assertEqual(stepper.height(), 30)
        self.assertEqual(stepper.sizePolicy().horizontalPolicy(), QSizePolicy.Expanding)

    def test_max_downloads_stepper_buttons_adjust_value_within_range(self):
        stepper = create_max_downloads_spin(3)
        buttons = stepper.findChildren(QPushButton)

        buttons[0].click()
        self.assertEqual(stepper.value(), 2)

        buttons[1].click()
        self.assertEqual(stepper.value(), 3)

        stepper.setValue(MAX_DOWNLOADS_RANGE[1] + 10)
        self.assertEqual(stepper.value(), MAX_DOWNLOADS_RANGE[1])

        stepper.setValue(MAX_DOWNLOADS_RANGE[0] - 10)
        self.assertEqual(stepper.value(), MAX_DOWNLOADS_RANGE[0])

    def test_max_downloads_stepper_accepts_direct_number_input(self):
        stepper = create_max_downloads_spin(3)
        input_box = stepper.findChild(QLineEdit)

        input_box.setText("7")
        input_box.editingFinished.emit()
        self.assertEqual(stepper.value(), 7)

        input_box.setText("99")
        input_box.editingFinished.emit()
        self.assertEqual(stepper.value(), MAX_DOWNLOADS_RANGE[1])

        input_box.setText("")
        input_box.editingFinished.emit()
        self.assertEqual(stepper.value(), MAX_DOWNLOADS_RANGE[0])

    def test_create_settings_button_does_not_capture_enter_as_default(self):
        button = create_settings_button(
            SettingsButtonSpec("Save", "save", "save"),
            {"save": ""},
            {"save": lambda: None},
        )

        self.assertFalse(button.isDefault())
        self.assertFalse(button.autoDefault())

    def test_create_settings_button_can_resize_to_text(self):
        button = create_settings_button(
            SettingsButtonSpec("Cancel", "cancel", "cancel"),
            {"cancel": ""},
            {"cancel": lambda: None},
            fixed_height=36,
            minimum_width_padding=SETTINGS_BUTTON_WIDTH_PADDING,
        )

        expected_width = (
            button.fontMetrics().boundingRect("Cancel").width()
            + SETTINGS_BUTTON_WIDTH_PADDING
        )
        self.assertEqual(button.minimumWidth(), expected_width)
        self.assertEqual(button.height(), 36)

    def test_create_login_row_resizes_login_button_to_text(self):
        row = create_login_row(
            "Cookies",
            "Sign in with a long translated label",
            lambda: None,
        )
        button = row.itemAt(row.count() - 1).widget()

        expected_width = (
            button.fontMetrics().boundingRect(button.text()).width()
            + TEXT_BUTTON_WIDTH_PADDING
        )
        self.assertEqual(button.minimumWidth(), expected_width)
        self.assertEqual(button.height(), SETTINGS_INPUT_HEIGHT)

    def test_create_login_row_can_add_logout_button(self):
        clicked = []
        row = create_login_row(
            "Cookies",
            "Login",
            lambda: clicked.append("login"),
            "Logout",
            lambda: clicked.append("logout"),
        )

        buttons = [
            row.itemAt(index).widget()
            for index in range(row.count())
            if isinstance(row.itemAt(index).widget(), QPushButton)
        ]
        self.assertEqual([button.text() for button in buttons], ["Login", "Logout"])
        buttons[1].click()
        self.assertEqual(clicked, ["logout"])

    def test_create_version_row_contains_label_and_value(self):
        row = create_version_row("Version", "1.2.3")

        self.assertEqual(row.itemAt(0).widget().text(), "Version")
        self.assertEqual(row.itemAt(1).widget().text(), "1.2.3")


if __name__ == "__main__":
    unittest.main()
