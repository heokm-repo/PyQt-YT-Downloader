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

from constants import (
    KEY_LANGUAGE,
    KEY_MAX_DOWNLOADS,
    KEY_THEME,
    KEY_USE_ACCELERATION,
    THEME_DARK,
    THEME_LIGHT,
)
from gui.settings.settings_apply_plan import build_settings_apply_plan
from locales import DEFAULT_LANGUAGE


class SettingsApplyPlanTests(unittest.TestCase):
    def test_build_settings_apply_plan_uses_selected_language(self):
        plan = build_settings_apply_plan({}, {KEY_LANGUAGE: "ko"})

        self.assertEqual(plan.language, "ko")

    def test_build_settings_apply_plan_defaults_language_when_missing(self):
        plan = build_settings_apply_plan({}, {})

        self.assertEqual(plan.language, DEFAULT_LANGUAGE)

    def test_build_settings_apply_plan_tracks_theme_change(self):
        plan = build_settings_apply_plan(
            {KEY_THEME: THEME_LIGHT},
            {KEY_THEME: THEME_DARK},
        )

        self.assertEqual(plan.theme, THEME_DARK)
        self.assertTrue(plan.theme_changed)

    def test_build_settings_apply_plan_ignores_unchanged_theme(self):
        plan = build_settings_apply_plan({}, {})

        self.assertEqual(plan.theme, THEME_LIGHT)
        self.assertFalse(plan.theme_changed)

    def test_build_settings_apply_plan_tracks_worker_count_change(self):
        plan = build_settings_apply_plan(
            {KEY_MAX_DOWNLOADS: 2, KEY_USE_ACCELERATION: False},
            {KEY_MAX_DOWNLOADS: 4, KEY_USE_ACCELERATION: False},
        )

        self.assertTrue(plan.adjust_worker_count)
        self.assertEqual(plan.worker_count, 4)

    def test_build_settings_apply_plan_uses_effective_worker_count(self):
        plan = build_settings_apply_plan(
            {KEY_MAX_DOWNLOADS: 2, KEY_USE_ACCELERATION: True},
            {KEY_MAX_DOWNLOADS: 9, KEY_USE_ACCELERATION: True},
        )

        self.assertFalse(plan.adjust_worker_count)
        self.assertEqual(plan.worker_count, 1)


if __name__ == "__main__":
    unittest.main()
