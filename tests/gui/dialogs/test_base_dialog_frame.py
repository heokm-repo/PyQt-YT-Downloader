import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QApplication

from gui.dialogs.base_dialog import BaseDialog
from gui.windowing.windows_custom_frame_mixin import (
    DEFAULT_RESIZE_CONTENT_MARGIN,
    WindowsCustomFrameMixin,
)


class BaseDialogFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_base_dialog_uses_shared_custom_frame_mixin(self):
        self.assertTrue(issubclass(BaseDialog, WindowsCustomFrameMixin))

    def test_fixed_dialog_keeps_native_resize_frame_disabled(self):
        with patch(
            "gui.windowing.windows_custom_frame_mixin.enable_windows_custom_frame"
        ) as enable_frame:
            dialog = BaseDialog()

        self.assertFalse(dialog._windows_custom_frame_enabled)
        self.assertEqual(
            dialog._windows_content_margin,
            DEFAULT_RESIZE_CONTENT_MARGIN,
        )
        enable_frame.assert_not_called()
        dialog.deleteLater()

    def test_resizable_dialog_enables_shared_native_frame(self):
        with (
            patch(
                "gui.windowing.windows_custom_frame_mixin.sys.platform",
                "win32",
            ),
            patch(
                "gui.windowing.windows_custom_frame_mixin.enable_windows_custom_frame",
                return_value=True,
            ) as enable_frame,
        ):
            dialog = BaseDialog(resizable=True)

        self.assertTrue(dialog._windows_custom_frame_enabled)
        self.assertIsNotNone(dialog.maximize_btn)
        enable_frame.assert_called_once_with(dialog)
        dialog.deleteLater()

    def test_window_state_changes_keep_layout_margins(self):
        dialog = BaseDialog(resizable=True)
        original = dialog._main_layout.contentsMargins()

        with patch.object(BaseDialog, "isMaximized", return_value=True):
            dialog.changeEvent(QEvent(QEvent.WindowStateChange))
        with (
            patch.object(BaseDialog, "isMaximized", return_value=False),
            patch.object(BaseDialog, "isMinimized", return_value=False),
        ):
            dialog.changeEvent(QEvent(QEvent.WindowStateChange))

        current = dialog._main_layout.contentsMargins()
        self.assertEqual(
            (current.left(), current.top(), current.right(), current.bottom()),
            (original.left(), original.top(), original.right(), original.bottom()),
        )
        dialog.deleteLater()


if __name__ == "__main__":
    unittest.main()
