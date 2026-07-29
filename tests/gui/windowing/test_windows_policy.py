import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import main


class WindowsPolicyTests(unittest.TestCase):
    def test_main_accepts_only_win32_platform(self):
        self.assertTrue(main.is_supported_platform("win32"))
        self.assertFalse(main.is_supported_platform("linux"))
        self.assertFalse(main.is_supported_platform("darwin"))


if __name__ == "__main__":
    unittest.main()
