import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from gui.settings.settings_update_check import (
    build_update_check_summary,
    format_update_check_message,
    run_update_check,
)
from gui.settings.settings_update_worker import SettingsUpdateWorker


ALL_PRESENT = {
    "yt-dlp": True,
    "ffmpeg": True,
    "ffprobe": True,
    "quickjs": True,
}


class SettingsUpdateCheckTests(unittest.TestCase):
    def test_all_current_components_produce_no_updates(self):
        summary = build_update_check_summary(
            (False, "2.1.2", "", None),
            {},
            ALL_PRESENT,
            "2.1.2",
        )

        self.assertFalse(summary.update_available)
        self.assertEqual(summary.updates, ())

    def test_ffmpeg_update_also_lists_ffprobe_shared_update(self):
        summary = build_update_check_summary(
            (True, "2.2.0", "https://example.test/app.exe", None),
            {"ffmpeg": {"current": "2026.01.01", "latest": "2026.07.01"}},
            ALL_PRESENT,
            "2.1.2",
        )

        self.assertEqual(
            [update.key for update in summary.updates],
            ["app", "ffmpeg", "ffprobe"],
        )
        self.assertEqual(summary.updates[1].current, "2026.01.01")
        self.assertEqual(summary.updates[2].latest, "2026.07.01")
        self.assertFalse(summary.updates[2].missing)

    def test_missing_ffprobe_is_reported_even_without_version_update(self):
        presence = {**ALL_PRESENT, "ffprobe": False}

        summary = build_update_check_summary(
            (False, "2.1.2", "", None),
            {},
            presence,
            "2.1.2",
        )

        self.assertEqual([update.key for update in summary.updates], ["ffprobe"])
        self.assertTrue(summary.updates[0].missing)

    def test_run_update_check_only_checks_and_does_not_apply(self):
        calls = []

        summary = run_update_check(
            lambda: calls.append("app") or (False, "2.1.2", "", None),
            lambda: calls.append("updates") or {},
            lambda: calls.append("presence") or ALL_PRESENT,
            "2.1.2",
        )

        self.assertFalse(summary.update_available)
        self.assertEqual(calls, ["presence", "updates", "app"])

    def test_message_includes_active_task_notice_only_when_needed(self):
        summary = build_update_check_summary(
            (False, "2.1.2", "", None),
            {"yt-dlp": {"current": "1", "latest": "2"}},
            ALL_PRESENT,
            "2.1.2",
        )

        without_tasks = format_update_check_message(
            summary,
            "Updates:",
            "\u2022 {name}: missing",
            "Restart required.",
            "Tasks will pause.",
            False,
        )
        with_tasks = format_update_check_message(
            summary,
            "Updates:",
            "\u2022 {name}: missing",
            "Restart required.",
            "Tasks will pause.",
            True,
        )

        self.assertIn("\u2022 yt-dlp: 1 \u2192 2", without_tasks)
        self.assertNotIn("Tasks will pause.", without_tasks)
        self.assertIn("Tasks will pause.", with_tasks)

    def test_worker_emits_combined_result(self):
        completed = []
        failures = []
        worker = SettingsUpdateWorker(
            "2.1.2",
            check_app_updates=lambda: (False, None, None, None),
            check_binary_updates=lambda: {},
            check_binary_presence=lambda: ALL_PRESENT,
        )
        worker.completed.connect(completed.append)
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(len(completed), 1)
        self.assertFalse(completed[0].update_available)
        self.assertEqual(failures, [])

    def test_worker_emits_failure_instead_of_up_to_date_result(self):
        completed = []
        failures = []

        def fail_binary_check():
            raise RuntimeError("network unavailable")

        worker = SettingsUpdateWorker(
            "2.1.2",
            check_app_updates=lambda: (False, None, None, None),
            check_binary_updates=fail_binary_check,
            check_binary_presence=lambda: ALL_PRESENT,
        )
        worker.completed.connect(completed.append)
        worker.failed.connect(failures.append)

        worker.run()

        self.assertEqual(completed, [])
        self.assertEqual(failures, ["network unavailable"])


if __name__ == "__main__":
    unittest.main()
