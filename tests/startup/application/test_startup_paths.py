import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from startup.paths import add_sys_path, initialize_startup_paths


class StartupPathsTests(unittest.TestCase):
    def test_add_sys_path_inserts_once(self):
        paths = ["existing"]

        self.assertTrue(add_sys_path("new", paths))
        self.assertFalse(add_sys_path("new", paths))

        self.assertEqual(paths, ["new", "existing"])

    def test_initialize_dev_paths_adds_main_directory(self):
        paths = []
        base_file = os.path.join("C:/project/src", "main.py")

        result = initialize_startup_paths(
            base_file,
            "src",
            frozen=False,
            sys_path=paths,
        )

        self.assertEqual(result.application_path, os.path.abspath("C:/project/src"))
        self.assertIsNone(result.bundled_src_path)
        self.assertEqual(paths, [os.path.abspath("C:/project/src")])

    def test_initialize_frozen_paths_preserves_pyinstaller_paths(self):
        paths = []
        meipass = os.path.abspath("C:/bundle")
        bundled_src = os.path.join(meipass, "src")

        result = initialize_startup_paths(
            "ignored.py",
            "src",
            frozen=True,
            meipass=meipass,
            path_exists=lambda path: path == bundled_src,
            sys_path=paths,
        )

        self.assertEqual(result.application_path, meipass)
        self.assertEqual(result.bundled_src_path, bundled_src)
        self.assertEqual(paths, [meipass, bundled_src])


if __name__ == "__main__":
    unittest.main()
