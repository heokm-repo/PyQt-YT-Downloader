import os
import sys
import unittest
from unittest.mock import Mock, patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from startup import binary_flow
from startup.binary_flow import (
    StartupCheckResult,
    format_binary_update_message,
    run_binary_update_prompt,
    run_missing_binary_repair,
    run_startup_checks,
)


class FakeLogger:
    def __init__(self):
        self.infos = []
        self.warnings = []

    def info(self, message):
        self.infos.append(message)

    def warning(self, message):
        self.warnings.append(message)


class FakeDialog:
    QUESTION = "question"
    instances = []
    next_result = 1

    def __init__(self, title, message, dialog_type, show_cancel=False):
        self.title = title
        self.message = message
        self.dialog_type = dialog_type
        self.show_cancel = show_cancel
        type(self).instances.append(self)

    def exec_(self):
        return type(self).next_result


class FakeProgressDialog:
    instances = []

    def __init__(self, update_mode=False, updates=None, binary_names=None):
        self.update_mode = update_mode
        self.updates = updates
        self.binary_names = binary_names
        self.download_success = True
        self.executed = False
        type(self).instances.append(self)

    def exec_(self):
        self.executed = True
        return 0


class StartupBinaryFlowTests(unittest.TestCase):
    def setUp(self):
        FakeDialog.instances = []
        FakeDialog.next_result = 1
        FakeProgressDialog.instances = []

    def test_run_startup_checks_preserves_failure_state(self):
        class FailedStartupDialog:
            updates_available = {}
            app_update_info = (False, None, None, None)
            check_failed = True
            check_error = "offline"

            def show(self):
                pass

            def start_checks(self):
                pass

            def exec_(self):
                return 0

        result = run_startup_checks(FailedStartupDialog)

        self.assertTrue(result.check_failed)
        self.assertEqual(result.error_message, "offline")

    def test_failed_update_check_does_not_report_binaries_up_to_date(self):
        logger = FakeLogger()
        show_error = Mock()
        startup_result = StartupCheckResult(
            updates_available={},
            app_update_info=(False, None, None, None),
            check_failed=True,
            error_message="offline",
        )
        presence = {
            "yt-dlp": True,
            "ffmpeg": True,
            "ffprobe": True,
            "quickjs": True,
        }

        with patch.object(binary_flow, "load_startup_language"), patch.object(
            binary_flow,
            "run_startup_checks",
            return_value=startup_result,
        ), patch(
            "utils.bin.manager.check_binary_presence",
            return_value=presence,
        ), patch.object(
            binary_flow,
            "run_binary_update_prompt",
        ) as update_prompt:
            result = binary_flow.run_startup_binary_flow(
                accepted_result=1,
                show_error_message=show_error,
                logger=logger,
            )

        self.assertEqual(result, startup_result.app_update_info)
        update_prompt.assert_not_called()
        self.assertIn(
            "Startup update checks did not complete: offline",
            logger.warnings,
        )
        self.assertNotIn("All binaries are up to date", logger.infos)

    def test_format_binary_update_message_lists_updates(self):
        message = format_binary_update_message(
            {"yt-dlp": {"current": "1", "latest": "2"}},
            "Updates:\n",
            "Update now?",
        )

        self.assertEqual(message, "Updates:\n\u2022 yt-dlp: 1 \u2192 2\nUpdate now?")

    def test_format_binary_update_message_names_ffprobe_with_ffmpeg(self):
        message = format_binary_update_message(
            {"ffmpeg": {"current": "1", "latest": "2"}},
            "Updates:\n",
            "Update now?",
        )

        self.assertEqual(
            message,
            "Updates:\n\u2022 FFmpeg / ffprobe: 1 \u2192 2\nUpdate now?",
        )

    def test_run_binary_update_prompt_runs_progress_when_accepted(self):
        logger = FakeLogger()

        run_binary_update_prompt(
            {"yt-dlp": {"current": "1", "latest": "2"}},
            accepted_result=1,
            logger=logger,
            message_dialog_factory=FakeDialog,
            progress_dialog_factory=FakeProgressDialog,
        )

        self.assertEqual(FakeDialog.instances[0].dialog_type, FakeDialog.QUESTION)
        self.assertFalse(FakeDialog.instances[0].show_cancel)
        progress = FakeProgressDialog.instances[0]
        self.assertTrue(progress.update_mode)
        self.assertTrue(progress.executed)
        self.assertIn("Update completed successfully", logger.infos)

    def test_run_binary_update_prompt_logs_skip_when_rejected(self):
        logger = FakeLogger()
        FakeDialog.next_result = 0

        run_binary_update_prompt(
            {"yt-dlp": {"current": "1", "latest": "2"}},
            accepted_result=1,
            logger=logger,
            message_dialog_factory=FakeDialog,
            progress_dialog_factory=FakeProgressDialog,
        )

        self.assertEqual(FakeProgressDialog.instances, [])
        self.assertIn("User skipped updates", logger.infos)

    def test_missing_binary_repair_passes_only_selected_bundle(self):
        logger = FakeLogger()

        run_missing_binary_repair(
            ("ffmpeg",),
            Mock(),
            logger,
            progress_dialog_factory=FakeProgressDialog,
        )

        progress = FakeProgressDialog.instances[0]
        self.assertEqual(progress.binary_names, ("ffmpeg",))
        self.assertTrue(progress.executed)
        self.assertIn("Missing binary repair completed successfully", logger.infos)

    def test_existing_install_missing_ffprobe_uses_repair_without_setup(self):
        logger = FakeLogger()
        show_error = Mock()
        startup_result = StartupCheckResult(
            updates_available={},
            app_update_info=(False, None, None, None),
        )
        presence = {
            "yt-dlp": True,
            "ffmpeg": True,
            "ffprobe": False,
            "quickjs": True,
        }

        with patch.object(binary_flow, "load_startup_language"), patch.object(
            binary_flow,
            "run_startup_checks",
            return_value=startup_result,
        ), patch(
            "utils.bin.manager.check_binary_presence",
            return_value=presence,
        ), patch(
            "utils.bin.manager.missing_binary_downloads",
            return_value=("ffmpeg",),
        ), patch.object(
            binary_flow,
            "run_missing_binary_repair",
        ) as repair, patch.object(
            binary_flow,
            "run_initial_binary_install",
        ) as initial_install, patch.object(
            binary_flow,
            "run_binary_update_prompt",
        ) as update_prompt:
            result = binary_flow.run_startup_binary_flow(
                accepted_result=1,
                show_error_message=show_error,
                logger=logger,
            )

        self.assertEqual(result, startup_result.app_update_info)
        repair.assert_called_once_with(("ffmpeg",), show_error, logger)
        initial_install.assert_not_called()
        update_prompt.assert_not_called()


if __name__ == "__main__":
    unittest.main()
