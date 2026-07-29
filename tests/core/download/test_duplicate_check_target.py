import os
import sys
import unittest
from dataclasses import dataclass
from typing import Optional

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from constants import DEFAULT_FORMAT
from gui.tasks.duplicate_check_target import (
    build_duplicate_check_target,
    build_duplicate_check_target_from_values,
    duplicate_target_format,
)


@dataclass
class FakeTask:
    video_id: Optional[str]
    extractor: str = "youtube"


class DuplicateCheckTargetTests(unittest.TestCase):
    def test_duplicate_target_format_uses_setting_or_default(self):
        self.assertEqual(duplicate_target_format({"format": "webm"}), "webm")
        self.assertEqual(duplicate_target_format({}), DEFAULT_FORMAT)
        self.assertEqual(duplicate_target_format(None), DEFAULT_FORMAT)

    def test_build_duplicate_check_target_from_values_normalizes_inputs(self):
        target = build_duplicate_check_target_from_values(
            "abc123", None, {"format": "webm"}
        )

        self.assertEqual(target.extractor, "unknown")
        self.assertEqual(target.video_id, "abc123")
        self.assertEqual(target.target_format, "webm")

    def test_build_duplicate_check_target_from_values_returns_none_without_video_id(self):
        self.assertIsNone(build_duplicate_check_target_from_values(None, "youtube", {}))

    def test_build_duplicate_check_target_returns_none_without_video_id(self):
        self.assertIsNone(build_duplicate_check_target(FakeTask(None), {"format": "mp4"}))

    def test_build_duplicate_check_target_uses_unknown_extractor_fallback(self):
        target = build_duplicate_check_target(FakeTask("abc123", ""), {"format": "mkv"})

        self.assertEqual(target.extractor, "unknown")
        self.assertEqual(target.video_id, "abc123")
        self.assertEqual(target.target_format, "mkv")


if __name__ == "__main__":
    unittest.main()