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

from gui.settings.settings_app_management import (
    build_error_message,
    build_uninstall_availability,
    build_uninstall_completion_result,
    is_development_environment,
    run_uninstall_flow,
)


class SettingsAppManagementTests(unittest.TestCase):
    def test_is_development_environment_inverts_frozen_flag(self):
        self.assertTrue(is_development_environment(False))
        self.assertFalse(is_development_environment(True))

    def test_build_uninstall_availability_blocks_development_mode(self):
        result = build_uninstall_availability(False, "dev mode")

        self.assertFalse(result.can_uninstall)
        self.assertEqual(result.message, "dev mode")

    def test_build_uninstall_availability_allows_packaged_mode(self):
        result = build_uninstall_availability(True, "dev mode")

        self.assertTrue(result.can_uninstall)
        self.assertIsNone(result.message)

    def test_build_uninstall_completion_result_for_started_uninstaller(self):
        result = build_uninstall_completion_result(True, "start failed")

        self.assertTrue(result.should_quit)
        self.assertIsNone(result.error_message)

    def test_build_uninstall_completion_result_for_start_failure(self):
        result = build_uninstall_completion_result(False, "start failed")

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "start failed")

    def test_run_uninstall_flow_stops_when_cancelled(self):
        calls = []

        result = run_uninstall_flow(
            lambda: False,
            True,
            lambda: calls.append("uninstall") or True,
            "dev mode",
            "start failed",
        )

        self.assertTrue(result.cancelled)
        self.assertFalse(result.should_quit)
        self.assertEqual(calls, [])

    def test_run_uninstall_flow_blocks_development_environment(self):
        calls = []

        result = run_uninstall_flow(
            lambda: True,
            False,
            lambda: calls.append("uninstall") or True,
            "dev mode",
            "start failed",
        )

        self.assertFalse(result.cancelled)
        self.assertEqual(result.development_message, "dev mode")
        self.assertFalse(result.should_quit)
        self.assertEqual(calls, [])

    def test_run_uninstall_flow_quits_when_uninstaller_starts(self):
        calls = []

        result = run_uninstall_flow(
            lambda: calls.append("confirm") or True,
            True,
            lambda: calls.append("uninstall") or True,
            "dev mode",
            "start failed",
        )

        self.assertTrue(result.should_quit)
        self.assertIsNone(result.error_message)
        self.assertEqual(calls, ["confirm", "uninstall"])

    def test_run_uninstall_flow_reports_uninstaller_start_failure(self):
        result = run_uninstall_flow(
            lambda: True,
            True,
            lambda: False,
            "dev mode",
            "start failed",
        )

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "start failed")

    def test_build_error_message_normalizes_error_to_string(self):
        message = build_error_message("failed: {error}", RuntimeError("boom"))

        self.assertEqual(message, "failed: boom")


if __name__ == "__main__":
    unittest.main()
