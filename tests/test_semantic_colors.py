import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from resources import colors


HEX_COLOR_PATTERN = re.compile(r"#[0-9a-fA-F]{3,8}\b")
NUMERIC_QCOLOR_PATTERN = re.compile(r"QColor\s*\(\s*\d+\s*,")
CSS_COLOR_FUNCTION_PATTERN = re.compile(
    r"\b(?:rgb|rgba|hsl|hsla)\s*\(\s*\d", re.IGNORECASE
)
NAMED_QSS_COLOR_PATTERN = re.compile(
    r"(?:background(?:-color)?|color|border(?:-[a-z]+)?):[^;\r\n]*"
    r"\b(?:white|black|red|green|blue|gray|grey|orange|yellow|transparent)\b",
    re.IGNORECASE,
)


class SemanticColorTests(unittest.TestCase):
    def test_palette_values_are_valid_colors(self):
        palette = {
            name: value
            for name, value in vars(colors).items()
            if name.startswith("COLOR_")
        }

        self.assertTrue(palette)
        for name, value in palette.items():
            with self.subTest(name=name):
                self.assertIsInstance(value, str)
                self.assertTrue(
                    value == "transparent" or HEX_COLOR_PATTERN.fullmatch(value),
                    f"{name} has an invalid color value: {value!r}",
                )

    def test_normalized_roles_share_the_selected_base_colors(self):
        self.assertEqual(colors.COLOR_SURFACE_SUBTLE, colors.COLOR_SURFACE_MUTED)
        self.assertEqual(colors.COLOR_DESTRUCTIVE_SURFACE, colors.COLOR_DANGER_SURFACE)
        self.assertEqual(
            colors.COLOR_CONTROL_SURFACE_EMPHASIS_PRESSED,
            colors.COLOR_CONTROL_SURFACE_PRESSED,
        )
        self.assertEqual(colors.COLOR_BORDER_STRONG, colors.COLOR_CONTROL_SURFACE_PRESSED)
        self.assertEqual(colors.COLOR_BORDER_PRESSED, colors.COLOR_CONTROL_SURFACE_PRESSED)
        self.assertEqual(
            colors.COLOR_CONTROL_SURFACE_PRESSED_STRONG,
            colors.COLOR_CONTROL_SURFACE_EMPHASIS_HOVER,
        )

    def test_ui_modules_do_not_hardcode_colors_outside_palette(self):
        palette_path = SRC / "resources" / "colors.py"
        violations = []

        for path in sorted(SRC.rglob("*.py")):
            if path == palette_path:
                continue
            source = path.read_text(encoding="utf-8")
            for line_number, line in enumerate(source.splitlines(), start=1):
                if (
                    HEX_COLOR_PATTERN.search(line)
                    or NUMERIC_QCOLOR_PATTERN.search(line)
                    or CSS_COLOR_FUNCTION_PATTERN.search(line)
                    or NAMED_QSS_COLOR_PATTERN.search(line)
                ):
                    violations.append(
                        f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}"
                    )

        self.assertEqual([], violations, "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
