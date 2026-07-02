import os
import sys
import unittest
from dataclasses import dataclass

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.dialogs.settings_fallback_notice import (
    build_download_folder_fallback_message,
    show_download_folder_fallback_notice,
)


@dataclass
class FakeNotice:
    original_path: str
    fallback_path: str
    reason: str


class FakeDialog:
    WARNING = "warning"
    instances = []

    def __init__(self, title, message, dialog_type, parent=None):
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.parent = parent
        self.executed = False
        type(self).instances.append(self)

    def exec_(self):
        self.executed = True
        return 0


class SettingsFallbackNoticeTests(unittest.TestCase):
    def setUp(self):
        FakeDialog.instances = []

    def test_build_download_folder_fallback_message_formats_notice_fields(self):
        message = build_download_folder_fallback_message(
            "old={old_path}; new={new_path}; reason={reason}",
            FakeNotice("C:/bad", "C:/good", "blocked"),
        )

        self.assertEqual(message, "old=C:/bad; new=C:/good; reason=blocked")

    def test_show_download_folder_fallback_notice_uses_warning_dialog(self):
        message = show_download_folder_fallback_notice(
            "parent",
            FakeNotice("C:/bad", "C:/good", "blocked"),
            "Warning",
            "old={old_path}; new={new_path}; reason={reason}",
            dialog_factory=FakeDialog,
        )

        self.assertEqual(message, "old=C:/bad; new=C:/good; reason=blocked")
        dialog = FakeDialog.instances[0]
        self.assertEqual(dialog.title, "Warning")
        self.assertEqual(dialog.message, message)
        self.assertEqual(dialog.dialog_type, FakeDialog.WARNING)
        self.assertEqual(dialog.parent, "parent")
        self.assertTrue(dialog.executed)


if __name__ == "__main__":
    unittest.main()
