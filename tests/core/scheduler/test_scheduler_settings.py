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

from constants import DEFAULT_MAX_DOWNLOADS, KEY_MAX_DOWNLOADS, KEY_USE_ACCELERATION
from core.scheduler_settings import should_adjust_worker_count, target_worker_count


class SchedulerSettingsTests(unittest.TestCase):
    def test_target_worker_count_uses_max_downloads_without_acceleration(self):
        self.assertEqual(target_worker_count({KEY_MAX_DOWNLOADS: 5}), 5)

    def test_target_worker_count_is_one_with_acceleration(self):
        self.assertEqual(target_worker_count({KEY_MAX_DOWNLOADS: 5, KEY_USE_ACCELERATION: True}), 1)

    def test_target_worker_count_uses_default_when_missing(self):
        self.assertEqual(target_worker_count({}), DEFAULT_MAX_DOWNLOADS)

    def test_should_adjust_worker_count_compares_effective_count(self):
        self.assertTrue(
            should_adjust_worker_count(
                {KEY_MAX_DOWNLOADS: 3, KEY_USE_ACCELERATION: False},
                {KEY_MAX_DOWNLOADS: 4, KEY_USE_ACCELERATION: False},
            )
        )
        self.assertFalse(
            should_adjust_worker_count(
                {KEY_MAX_DOWNLOADS: 3, KEY_USE_ACCELERATION: True},
                {KEY_MAX_DOWNLOADS: 9, KEY_USE_ACCELERATION: True},
            )
        )


if __name__ == "__main__":
    unittest.main()
