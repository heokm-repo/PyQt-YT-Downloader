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

from constants import (
    KEY_AUDIO_QUALITY,
    KEY_DOWNLOAD_FOLDER,
    KEY_FORMAT,
    KEY_LANGUAGE,
    KEY_MAX_DOWNLOADS,
    KEY_NORMALIZE_AUDIO,
    KEY_USE_ACCELERATION,
    KEY_VIDEO_QUALITY,
)
from gui.settings.settings_form_data import (
    build_settings_from_form_values,
    language_code_at_index,
    language_display_options,
    language_index_for_code,
    normalize_download_folder_input,
    is_download_folder_input_valid,
)


class SettingsFormDataTests(unittest.TestCase):
    def test_language_code_at_index_returns_supported_language_or_default(self):
        supported = {"ko": "Korean", "en": "English"}

        self.assertEqual(language_code_at_index(1, supported, "ko"), "en")
        self.assertEqual(language_code_at_index(99, supported, "ko"), "ko")

    def test_language_display_options_formats_supported_languages(self):
        supported = {"ko": "Korean", "en": "English"}

        self.assertEqual(
            language_display_options(supported), ["ko - Korean", "en - English"]
        )

    def test_language_index_for_code_returns_matching_index_or_zero(self):
        supported = {"ko": "Korean", "en": "English"}

        self.assertEqual(language_index_for_code("en", supported), 1)
        self.assertEqual(language_index_for_code("missing", supported), 0)
        self.assertEqual(language_index_for_code(None, supported), 0)

    def test_normalize_download_folder_input_strips_text(self):
        self.assertEqual(normalize_download_folder_input("  C:/Downloads  "), "C:/Downloads")
        self.assertEqual(normalize_download_folder_input(None), "")

    def test_is_download_folder_input_valid_requires_non_empty_text(self):
        self.assertTrue(is_download_folder_input_valid(" C:/Downloads "))
        self.assertFalse(is_download_folder_input_valid("   "))
        self.assertFalse(is_download_folder_input_valid(None))

    def test_build_settings_from_form_values_updates_known_keys_and_preserves_extra(self):
        settings = build_settings_from_form_values(
            {"extra": "keep"},
            "C:/Downloads",
            "1080p",
            "320k",
            "mp4",
            True,
            False,
            4,
            0,
        )

        self.assertEqual(settings["extra"], "keep")
        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], "C:/Downloads")
        self.assertEqual(settings[KEY_VIDEO_QUALITY], "1080p")
        self.assertEqual(settings[KEY_AUDIO_QUALITY], "320k")
        self.assertEqual(settings[KEY_FORMAT], "mp4")
        self.assertTrue(settings[KEY_NORMALIZE_AUDIO])
        self.assertFalse(settings[KEY_USE_ACCELERATION])
        self.assertEqual(settings[KEY_MAX_DOWNLOADS], 4)
        self.assertIn(KEY_LANGUAGE, settings)


if __name__ == "__main__":
    unittest.main()
