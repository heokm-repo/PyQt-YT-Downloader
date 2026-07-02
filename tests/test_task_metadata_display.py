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

from gui.tasks.task_metadata_display import (
    DEFAULT_TITLE,
    DEFAULT_UPLOADER,
    build_task_metadata_display,
    format_task_title,
)


class TaskMetadataDisplayTests(unittest.TestCase):
    def test_format_task_title_uses_uppercase_selected_format(self):
        self.assertEqual(format_task_title("Video", {"format": "webm"}), "[WEBM] Video")

    def test_format_task_title_defaults_to_mp4(self):
        self.assertEqual(format_task_title("Video", {}), "[MP4] Video")
        self.assertEqual(format_task_title("Video", None), "[MP4] Video")

    def test_build_task_metadata_display_maps_labels(self):
        display = build_task_metadata_display(
            {
                "title": "Example",
                "uploader": "Channel",
                "file_size": 2048,
                "thumbnail": "https://example.invalid/thumb.jpg",
            },
            {"format": "mp3"},
        )

        self.assertEqual(display.title_text, "[MP3] Example")
        self.assertEqual(display.uploader_text, "Channel")
        self.assertEqual(display.file_size_text, "2.00 KiB")
        self.assertEqual(display.thumbnail_url, "https://example.invalid/thumb.jpg")

    def test_build_task_metadata_display_uses_defaults(self):
        display = build_task_metadata_display({}, {"format": "mp4"})

        self.assertEqual(display.title_text, f"[MP4] {DEFAULT_TITLE}")
        self.assertEqual(display.uploader_text, DEFAULT_UPLOADER)
        self.assertIsNone(display.file_size_text)
        self.assertIsNone(display.thumbnail_url)

    def test_build_task_metadata_display_formats_present_null_file_size(self):
        display = build_task_metadata_display({"file_size": None}, {"format": "mp4"})

        self.assertEqual(display.file_size_text, "0 B")


if __name__ == "__main__":
    unittest.main()