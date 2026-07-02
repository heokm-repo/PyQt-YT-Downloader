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

from PyQt5.QtWidgets import QDialog

from gui.dialogs.main_window_messages import (
    ask_duplicate_confirmation_dialog,
    confirm_resume_paused_tasks_dialog,
    playlist_error_text,
    show_no_new_videos_dialog,
    show_playlist_error_dialog,
)


class FakeDialog:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    QUESTION = "question"

    instances = []
    next_result = QDialog.Accepted

    def __init__(self, title, message, dialog_type, parent=None, show_cancel=False):
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.parent = parent
        self.show_cancel = show_cancel
        type(self).instances.append(self)

    def exec_(self):
        return type(self).next_result


class MainWindowDialogsTests(unittest.TestCase):
    def setUp(self):
        FakeDialog.instances = []
        FakeDialog.next_result = QDialog.Accepted

    def test_playlist_error_text_uses_fallback_when_error_is_empty(self):
        self.assertEqual(playlist_error_text("", "Fallback"), "Fallback")

    def test_playlist_error_text_prefers_explicit_error(self):
        self.assertEqual(playlist_error_text("Network failed", "Fallback"), "Network failed")

    def test_show_playlist_error_dialog_uses_warning_type(self):
        message = show_playlist_error_dialog(
            "parent",
            "Playlist Error",
            "",
            "Could not fetch",
            dialog_factory=FakeDialog,
        )

        self.assertEqual(message, "Could not fetch")
        dialog = FakeDialog.instances[0]
        self.assertEqual(dialog.title, "Playlist Error")
        self.assertEqual(dialog.message, "Could not fetch")
        self.assertEqual(dialog.dialog_type, FakeDialog.WARNING)
        self.assertEqual(dialog.parent, "parent")

    def test_ask_duplicate_confirmation_formats_message_and_returns_acceptance(self):
        accepted = ask_duplicate_confirmation_dialog(
            "parent",
            10,
            3,
            "Duplicate",
            "{duplicate}/{total}",
            dialog_factory=FakeDialog,
        )

        self.assertTrue(accepted)
        dialog = FakeDialog.instances[0]
        self.assertEqual(dialog.message, "3/10")
        self.assertEqual(dialog.dialog_type, FakeDialog.QUESTION)
        self.assertFalse(dialog.show_cancel)

    def test_ask_duplicate_confirmation_returns_false_when_rejected(self):
        FakeDialog.next_result = QDialog.Rejected

        accepted = ask_duplicate_confirmation_dialog(
            "parent",
            10,
            3,
            "Duplicate",
            "{duplicate}/{total}",
            dialog_factory=FakeDialog,
        )

        self.assertFalse(accepted)

    def test_show_no_new_videos_dialog_uses_info_type(self):
        show_no_new_videos_dialog("parent", "Notice", "No items", dialog_factory=FakeDialog)

        dialog = FakeDialog.instances[0]
        self.assertEqual(dialog.title, "Notice")
        self.assertEqual(dialog.message, "No items")
        self.assertEqual(dialog.dialog_type, FakeDialog.INFO)

    def test_confirm_resume_paused_tasks_dialog_returns_acceptance(self):
        accepted = confirm_resume_paused_tasks_dialog(
            "parent",
            "Resume",
            "Resume tasks?",
            dialog_factory=FakeDialog,
        )

        self.assertTrue(accepted)
        dialog = FakeDialog.instances[0]
        self.assertEqual(dialog.dialog_type, FakeDialog.QUESTION)
        self.assertFalse(dialog.show_cancel)


if __name__ == "__main__":
    unittest.main()