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

from gui.settings.settings_button_specs import (
    SettingsButtonSpec,
    build_app_management_button_specs,
    build_dialog_action_button_specs,
)


class SettingsButtonSpecsTests(unittest.TestCase):
    def test_build_app_management_button_specs_returns_expected_order(self):
        specs = build_app_management_button_specs(
            "Update", "License", "Sponsor", "Uninstall"
        )

        self.assertEqual(
            specs,
            [
                SettingsButtonSpec("Update", "check_update", "update"),
                SettingsButtonSpec("License", "license", "update"),
                SettingsButtonSpec("Sponsor", "sponsor", "update"),
                SettingsButtonSpec("Uninstall", "uninstall", "uninstall"),
            ],
        )

    def test_build_dialog_action_button_specs_returns_footer_actions(self):
        specs = build_dialog_action_button_specs("Cancel", "Save")

        self.assertEqual(
            specs,
            [
                SettingsButtonSpec("Cancel", "cancel", "cancel"),
                SettingsButtonSpec("Save", "save", "save"),
            ],
        )


if __name__ == "__main__":
    unittest.main()