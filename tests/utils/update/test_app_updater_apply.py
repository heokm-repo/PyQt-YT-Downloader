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

from constants import INNO_SETUP_INSTALL_ARGS, INNO_SETUP_RUN_AFTER_INSTALL_ARG
from utils.app_updater import apply_update


class AppUpdaterApplyTests(unittest.TestCase):
    def test_apply_update_starts_installer_with_relaunch_arg(self):
        previous_frozen = getattr(sys, "frozen", None)
        sys.frozen = True
        try:
            with patch("utils.app_updater.os.path.exists", return_value=True), patch(
                "utils.app_updater.subprocess.Popen"
            ) as popen, patch(
                "utils.app_updater.verify_sha256",
                return_value=True,
            ) as verify:
                digest = "sha256:" + "a" * 64
                self.assertTrue(apply_update("setup.exe", digest))

            command = popen.call_args.args[0]
            self.assertEqual(command, ["setup.exe", *INNO_SETUP_INSTALL_ARGS])
            self.assertIn(INNO_SETUP_RUN_AFTER_INSTALL_ARG, command)
            verify.assert_called_once_with("setup.exe", digest)
        finally:
            if previous_frozen is None:
                delattr(sys, "frozen")
            else:
                sys.frozen = previous_frozen


if __name__ == "__main__":
    unittest.main()
