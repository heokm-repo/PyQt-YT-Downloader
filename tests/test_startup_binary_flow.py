import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from startup.binary_flow import format_binary_update_message, run_binary_update_prompt


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

    def __init__(self, update_mode=False, updates=None):
        self.update_mode = update_mode
        self.updates = updates
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

    def test_format_binary_update_message_lists_updates(self):
        message = format_binary_update_message(
            {"yt-dlp": {"current": "1", "latest": "2"}},
            "Updates:\n",
            "Update now?",
        )

        self.assertEqual(message, "Updates:\n\u2022 yt-dlp: 1 \u2192 2\nUpdate now?")

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


if __name__ == "__main__":
    unittest.main()
