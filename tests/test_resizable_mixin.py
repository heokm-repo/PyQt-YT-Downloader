import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.windowing.resizable_mixin import _point_from_lparam, _signed_word


def make_lparam(x, y):
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


class ResizableMixinTests(unittest.TestCase):
    def test_signed_word_handles_multimonitor_negative_coordinates(self):
        self.assertEqual(_signed_word(0xFFFF), -1)
        self.assertEqual(_signed_word(0x8000), -32768)
        self.assertEqual(_signed_word(100), 100)

    def test_point_from_lparam_returns_signed_global_point(self):
        point = _point_from_lparam(make_lparam(-12, 34))

        self.assertEqual(point.x(), -12)
        self.assertEqual(point.y(), 34)


if __name__ == "__main__":
    unittest.main()
