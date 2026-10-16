import os
import sys
import unittest
from unittest.mock import Mock, patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "src")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from constants import THEME_DARK, THEME_LIGHT
from gui.theme import apply_application_theme
from resources import colors, styles


class ThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def tearDown(self):
        apply_application_theme(THEME_LIGHT)

    def test_dark_palette_keeps_dependent_aliases_bound_to_base_roles(self):
        palette = colors.theme_colors(THEME_DARK)

        self.assertEqual(palette["COLOR_ON_ACCENT"], palette["COLOR_SURFACE"])
        self.assertEqual(palette["COLOR_ICON_DEFAULT"], palette["COLOR_TEXT_DEFAULT"])
        self.assertEqual(palette["COLOR_DIVIDER"], palette["COLOR_BORDER"])

    def test_applying_theme_rebuilds_stylesheets(self):
        styles.apply_theme(THEME_LIGHT)
        light_style = str(styles.CENTRAL_WIDGET_STYLE)

        styles.apply_theme(THEME_DARK)
        dark_style = str(styles.CENTRAL_WIDGET_STYLE)

        self.assertNotEqual(light_style, dark_style)
        self.assertIn(colors.COLOR_SURFACE, dark_style)

    def test_application_palette_uses_active_semantic_colors(self):
        active_theme = apply_application_theme(THEME_DARK)
        palette = self.app.palette()

        self.assertEqual(active_theme, THEME_DARK)
        self.assertEqual(
            palette.color(QPalette.Window),
            QColor(colors.COLOR_SURFACE),
        )
        self.assertEqual(
            palette.color(QPalette.HighlightedText),
            QColor(colors.COLOR_ON_ACCENT),
        )

    def test_repeated_theme_reuses_stylesheet_objects(self):
        styles.apply_theme(THEME_DARK)
        first = styles.CENTRAL_WIDGET_STYLE
        styles.apply_theme(THEME_DARK)
        self.assertIs(styles.CENTRAL_WIDGET_STYLE, first)
        styles.apply_theme(THEME_LIGHT)
        self.assertIsNot(styles.CENTRAL_WIDGET_STYLE, first)

    def test_cached_qss_still_applies_palette_to_new_application(self):
        # Exercise the pre-QApplication call followed by two application lifetimes.
        with patch('gui.theme.QApplication') as application:
            application.instance.return_value = None
            apply_application_theme(THEME_DARK)
            first_style = styles.CENTRAL_WIDGET_STYLE
            for app in (Mock(), Mock()):
                application.instance.return_value = app
                apply_application_theme(THEME_DARK)
                app.setPalette.assert_called_once()
                palette = app.setPalette.call_args.args[0]
                self.assertEqual(palette.color(QPalette.Window), QColor(colors.COLOR_SURFACE))
                self.assertIs(styles.CENTRAL_WIDGET_STYLE, first_style)


if __name__ == "__main__":
    unittest.main()
