import json
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA

import sys
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import DEFAULT_THEME, KEY_DOWNLOAD_FOLDER, KEY_THEME, THEME_DARK
from utils import settings_store


class SettingsStoreTests(unittest.TestCase):
    def setUp(self):
        settings_store.consume_download_folder_fallback_notice()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.user_data = os.path.join(self.tmp.name, "appdata")
        self.base_path = os.path.join(self.tmp.name, "base")
        self.home_path = os.path.join(self.tmp.name, "home")
        os.makedirs(self.user_data, exist_ok=True)
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(self.home_path, exist_ok=True)

        self.patches = [
            patch.object(settings_store, "get_user_data_path", return_value=self.user_data),
            patch.object(settings_store, "get_base_path", return_value=self.base_path),
            patch.object(settings_store.Path, "home", return_value=settings_store.Path(self.home_path)),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def _settings_file(self):
        return os.path.join(self.user_data, settings_store.SETTINGS_FILENAME)

    def test_load_settings_creates_default_download_folder(self):
        settings = settings_store.load_settings()

        expected = os.path.join(self.base_path, "YTDownloader")
        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], expected)
        self.assertTrue(os.path.isdir(expected))
        self.assertIsNone(settings_store.consume_download_folder_fallback_notice())
        self.assertEqual(settings[KEY_THEME], DEFAULT_THEME)

    def test_load_settings_normalizes_and_persists_invalid_theme(self):
        download_path = os.path.join(self.tmp.name, "downloads")
        os.makedirs(download_path, exist_ok=True)
        with open(self._settings_file(), "w", encoding="utf-8") as f:
            json.dump(
                {KEY_DOWNLOAD_FOLDER: download_path, KEY_THEME: "invalid"},
                f,
            )

        settings = settings_store.load_settings()

        self.assertEqual(settings[KEY_THEME], DEFAULT_THEME)
        with open(self._settings_file(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved[KEY_THEME], DEFAULT_THEME)

    def test_save_settings_preserves_supported_theme(self):
        settings = {
            KEY_DOWNLOAD_FOLDER: os.path.join(self.tmp.name, "downloads"),
            KEY_THEME: THEME_DARK,
        }

        settings_store.save_settings(settings)

        self.assertEqual(settings[KEY_THEME], THEME_DARK)

    def test_load_settings_migrates_legacy_save_path_to_download_folder(self):
        legacy_path = os.path.join(self.tmp.name, "legacy")
        os.makedirs(legacy_path, exist_ok=True)
        with open(self._settings_file(), "w", encoding="utf-8") as f:
            json.dump({"save_path": legacy_path}, f)

        settings = settings_store.load_settings()

        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], legacy_path)
        self.assertNotIn("save_path", settings)
        with open(self._settings_file(), "r", encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved[KEY_DOWNLOAD_FOLDER], legacy_path)
        self.assertNotIn("save_path", saved)

    def test_failed_download_folder_falls_back_and_records_notice(self):
        bad_path = os.path.join(self.tmp.name, "bad")
        fallback_path = os.path.join(self.home_path, "Downloads", "YTDownloader")

        with patch.object(settings_store, "_ensure_writable_folder") as ensure:
            ensure.side_effect = [(False, "blocked"), (True, "")]
            settings = {KEY_DOWNLOAD_FOLDER: bad_path}
            settings_store.save_settings(settings)

        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], fallback_path)
        notice = settings_store.consume_download_folder_fallback_notice()
        self.assertIsNotNone(notice)
        self.assertEqual(notice.original_path, bad_path)
        self.assertEqual(notice.fallback_path, fallback_path)
        self.assertEqual(notice.reason, "blocked")

    def test_windows_protected_folder_falls_back_without_write_probe(self):
        fallback_path = os.path.join(self.home_path, "Downloads", "YTDownloader")
        settings = {KEY_DOWNLOAD_FOLDER: r"C:\Program Files (x86)"}

        with patch.object(settings_store.os, "name", "nt"), patch.dict(
            settings_store.os.environ,
            {
                "SystemDrive": "C:",
                "ProgramFiles": r"C:\Program Files",
                "ProgramFiles(x86)": r"C:\Program Files (x86)",
                "SystemRoot": r"C:\Windows",
            },
            clear=False,
        ):
            settings_store.save_settings(settings)

        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], fallback_path)
        notice = settings_store.consume_download_folder_fallback_notice()
        self.assertIsNotNone(notice)
        self.assertEqual(notice.original_path, r"C:\Program Files (x86)")
        self.assertEqual(notice.fallback_path, fallback_path)
        self.assertIn("Protected Windows", notice.reason)

    def test_get_download_folder_migrates_legacy_key_in_place(self):
        settings = {"save_path": "C:/old"}

        folder = settings_store.get_download_folder(settings)

        self.assertEqual(folder, "C:/old")
        self.assertEqual(settings[KEY_DOWNLOAD_FOLDER], "C:/old")
        self.assertNotIn("save_path", settings)


if __name__ == "__main__":
    unittest.main()
