import os
import sys
import unittest
from unittest.mock import patch


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.workers import StartupWorker


class StartupWorkerTests(unittest.TestCase):
    def test_binary_network_failure_emits_error_without_completed_results(self):
        completed = []
        errors = []
        worker = StartupWorker()
        worker.finished_checks.connect(
            lambda binary_updates, app_update: completed.append(
                (binary_updates, app_update)
            )
        )
        worker.error_occurred.connect(errors.append)

        with patch(
            "core.workers.STARTUP_STATUS_SETTLE_DELAY_SEC",
            0,
        ), patch(
            "utils.bin.manager.check_binaries_exist",
            return_value=True,
        ), patch(
            "utils.bin.manager.check_updates_available_strict",
            side_effect=RuntimeError("offline"),
        ), patch(
            "utils.app_updater.check_for_updates_strict",
        ) as app_check:
            worker.run()

        self.assertEqual(completed, [])
        self.assertEqual(errors, ["offline"])
        app_check.assert_not_called()

    def test_successful_strict_checks_emit_collected_results(self):
        completed = []
        errors = []
        worker = StartupWorker()
        worker.finished_checks.connect(
            lambda binary_updates, app_update: completed.append(
                (binary_updates, app_update)
            )
        )
        worker.error_occurred.connect(errors.append)
        binary_updates = {
            "yt-dlp": {"current": "1", "latest": "2"},
        }
        app_update = (False, None, None, None)

        with patch(
            "core.workers.STARTUP_STATUS_SETTLE_DELAY_SEC",
            0,
        ), patch(
            "utils.bin.manager.check_binaries_exist",
            return_value=True,
        ), patch(
            "utils.bin.manager.check_updates_available_strict",
            return_value=binary_updates,
        ), patch(
            "utils.app_updater.check_for_updates_strict",
            return_value=app_update,
        ):
            worker.run()

        self.assertEqual(completed, [(binary_updates, app_update)])
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
