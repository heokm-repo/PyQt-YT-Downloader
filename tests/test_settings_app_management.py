import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
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
    build_update_available_message,
    build_update_check_result,
    build_update_completion_result,
    is_development_environment,
    run_uninstall_flow,
    run_update_flow,
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

    def test_build_update_available_message_formats_versions(self):
        message = build_update_available_message("{current} -> {latest}", "v1", "v2")

        self.assertEqual(message, "v1 -> v2")

    def test_build_error_message_normalizes_error_to_string(self):
        message = build_error_message("failed: {error}", RuntimeError("boom"))

        self.assertEqual(message, "failed: boom")

    def test_build_update_check_result_for_latest_version(self):
        result = build_update_check_result(
            False,
            "v1",
            "https://example.invalid/app.exe",
            "v1",
            "Already latest",
            "{current} -> {latest}",
        )

        self.assertFalse(result.update_available)
        self.assertEqual(result.message, "Already latest")
        self.assertEqual(result.latest_version, "v1")
        self.assertEqual(result.download_url, "https://example.invalid/app.exe")

    def test_build_update_check_result_for_available_update(self):
        result = build_update_check_result(
            True,
            "v2",
            "https://example.invalid/app.exe",
            "v1",
            "Already latest",
            "{current} -> {latest}",
        )

        self.assertTrue(result.update_available)
        self.assertEqual(result.message, "v1 -> v2")

    def test_build_update_completion_result_for_download_failure(self):
        result = build_update_completion_result(
            None, False, "download failed", "apply failed"
        )

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "download failed")

    def test_build_update_completion_result_for_apply_failure(self):
        result = build_update_completion_result(
            "new.exe", False, "download failed", "apply failed"
        )

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "apply failed")

    def test_build_update_completion_result_for_success(self):
        result = build_update_completion_result(
            "new.exe", True, "download failed", "apply failed"
        )

        self.assertTrue(result.should_quit)
        self.assertIsNone(result.error_message)

    def test_run_update_flow_reports_latest_version_without_side_effects(self):
        calls = []

        result = run_update_flow(
            lambda: (False, "v1", ""),
            lambda url: calls.append(("download", url)) or "new.exe",
            lambda path: calls.append(("apply", path)) or True,
            lambda update_result: calls.append(("confirm", update_result.message)) or True,
            "v1",
            "Already latest",
            "{current} -> {latest}",
            "download failed",
            "apply failed",
        )

        self.assertFalse(result.update_available)
        self.assertFalse(result.should_quit)
        self.assertEqual(result.check_result.message, "Already latest")
        self.assertEqual(calls, [])

    def test_run_update_flow_stops_when_update_is_cancelled(self):
        calls = []

        result = run_update_flow(
            lambda: (True, "v2", "https://example.test/app.exe"),
            lambda url: calls.append(("download", url)) or "new.exe",
            lambda path: calls.append(("apply", path)) or True,
            lambda update_result: calls.append(("confirm", update_result.message)) or False,
            "v1",
            "Already latest",
            "{current} -> {latest}",
            "download failed",
            "apply failed",
        )

        self.assertTrue(result.update_available)
        self.assertTrue(result.cancelled)
        self.assertFalse(result.should_quit)
        self.assertEqual(calls, [("confirm", "v1 -> v2")])

    def test_run_update_flow_downloads_and_applies_confirmed_update(self):
        calls = []

        result = run_update_flow(
            lambda: (True, "v2", "https://example.test/app.exe"),
            lambda url: calls.append(("download", url)) or "new.exe",
            lambda path: calls.append(("apply", path)) or True,
            lambda update_result: calls.append(("confirm", update_result.message)) or True,
            "v1",
            "Already latest",
            "{current} -> {latest}",
            "download failed",
            "apply failed",
        )

        self.assertTrue(result.should_quit)
        self.assertIsNone(result.error_message)
        self.assertEqual(
            calls,
            [
                ("confirm", "v1 -> v2"),
                ("download", "https://example.test/app.exe"),
                ("apply", "new.exe"),
            ],
        )

    def test_run_update_flow_reports_download_failure(self):
        calls = []

        result = run_update_flow(
            lambda: (True, "v2", "https://example.test/app.exe"),
            lambda url: calls.append(("download", url)) or None,
            lambda path: calls.append(("apply", path)) or True,
            lambda update_result: True,
            "v1",
            "Already latest",
            "{current} -> {latest}",
            "download failed",
            "apply failed",
        )

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "download failed")
        self.assertEqual(calls, [("download", "https://example.test/app.exe")])

    def test_run_update_flow_reports_apply_failure(self):
        result = run_update_flow(
            lambda: (True, "v2", "https://example.test/app.exe"),
            lambda url: "new.exe",
            lambda path: False,
            lambda update_result: True,
            "v1",
            "Already latest",
            "{current} -> {latest}",
            "download failed",
            "apply failed",
        )

        self.assertFalse(result.should_quit)
        self.assertEqual(result.error_message, "apply failed")


if __name__ == "__main__":
    unittest.main()