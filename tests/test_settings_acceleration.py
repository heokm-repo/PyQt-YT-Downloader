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

from gui.settings.settings_acceleration import max_downloads_state_for_acceleration


class SettingsAccelerationTests(unittest.TestCase):
    def test_max_downloads_state_for_enabled_acceleration_locks_to_one(self):
        state = max_downloads_state_for_acceleration(True)

        self.assertFalse(state.enabled)
        self.assertEqual(state.value, 1)

    def test_max_downloads_state_for_disabled_acceleration_keeps_current_value(self):
        state = max_downloads_state_for_acceleration(False)

        self.assertTrue(state.enabled)
        self.assertIsNone(state.value)


if __name__ == "__main__":
    unittest.main()