import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.windowing.high_dpi import configure_qt_display_policy


class FakeQt:
    AA_DisableHighDpiScaling = "disable-scaling"


class FakeApplication:
    attributes = []

    @classmethod
    def setAttribute(cls, attribute, enabled):
        cls.attributes.append((attribute, enabled))


class DisplayPolicyTests(unittest.TestCase):
    def setUp(self):
        FakeApplication.attributes = []

    def test_uses_native_geometry(self):
        configure_qt_display_policy(FakeApplication, FakeQt)

        self.assertEqual(
            FakeApplication.attributes,
            [(FakeQt.AA_DisableHighDpiScaling, True)],
        )


if __name__ == "__main__":
    unittest.main()
