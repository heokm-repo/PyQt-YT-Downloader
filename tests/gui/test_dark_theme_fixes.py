import os
import sys
import unittest
from dataclasses import dataclass


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtWidgets import QApplication, QWidget

from constants import THEME_DARK, THEME_LIGHT, TaskStatus
from gui.settings.settings_checkbox import SettingsCheckBox
from gui.settings.settings_controls import create_settings_checkbox
from gui.tasks.context_menu import ContextMenuBuilder
from gui.theme import apply_application_theme
from gui.widgets.toggle_button import ToggleButton
from resources import colors, styles


@dataclass
class FakeTask:
    status: TaskStatus
    output_path: str = ""


class DarkThemeFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        apply_application_theme(THEME_DARK)

    def tearDown(self):
        apply_application_theme(THEME_LIGHT)

    def test_global_toggle_uses_its_darker_dedicated_surface(self):
        button = ToggleButton()

        self.assertIn(colors.COLOR_GLOBAL_TOGGLE_ACTIVE_SURFACE, button.styleSheet())
        self.assertNotEqual(
            colors.COLOR_GLOBAL_TOGGLE_ACTIVE_SURFACE,
            colors.COLOR_TASK_DOWNLOADING_BORDER,
        )

    def test_task_context_menu_uses_thin_semantic_border(self):
        parent = QWidget()
        parent.tasks = [FakeTask(TaskStatus.FINISHED)]
        menu = ContextMenuBuilder(parent).build(
            parent.tasks,
            {
                "play": lambda: None,
                "open_folder": lambda: None,
                "copy_url": lambda: None,
                "retry": lambda: None,
                "delete_file": lambda: None,
                "remove": lambda: None,
                "remove_all_completed": lambda: None,
            },
        )

        self.assertEqual(menu.styleSheet(), styles.TASK_CONTEXT_MENU_STYLE)
        self.assertIn(f"border: 1px solid {colors.COLOR_BORDER}", menu.styleSheet())

    def test_settings_checkbox_uses_theme_aware_renderer(self):
        checkbox = create_settings_checkbox(False)

        self.assertIsInstance(checkbox, SettingsCheckBox)
        self.assertEqual((checkbox.width(), checkbox.height()), (20, 20))


if __name__ == "__main__":
    unittest.main()
