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

from constants import DEFAULT_FORMAT
from gui.settings.settings_format_options import (
    build_format_combo_entries,
    normalize_format_selection,
    quality_control_state_for_format,
)


class SettingsFormatOptionsTests(unittest.TestCase):
    def test_build_format_combo_entries_orders_headers_and_formats(self):
        entries = build_format_combo_entries("Video", "Audio", ["mp4"], ["mp3", "wav"])

        self.assertEqual([entry.label for entry in entries], ["Video", "mp4", "Audio", "mp3", "wav"])
        self.assertEqual([entry.is_header for entry in entries], [True, False, True, False, False])

    def test_normalize_format_selection_keeps_known_format(self):
        self.assertEqual(normalize_format_selection("webm"), "webm")

    def test_normalize_format_selection_falls_back_for_unknown_format(self):
        self.assertEqual(normalize_format_selection("unknown"), DEFAULT_FORMAT)

    def test_quality_controls_follow_selected_format_semantics(self):
        mp4 = quality_control_state_for_format("mp4")
        mp3 = quality_control_state_for_format("mp3")
        wav = quality_control_state_for_format("wav")

        self.assertTrue(mp4.video_quality_enabled)
        self.assertTrue(mp4.audio_quality_enabled)
        self.assertFalse(mp3.video_quality_enabled)
        self.assertTrue(mp3.audio_quality_enabled)
        self.assertFalse(wav.video_quality_enabled)
        self.assertFalse(wav.audio_quality_enabled)


if __name__ == "__main__":
    unittest.main()
