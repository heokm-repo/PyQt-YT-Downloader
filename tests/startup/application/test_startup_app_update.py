import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from startup.app_update import download_app_update


class FakeApplication:
    def __init__(self):
        self.processed_events = 0

    def processEvents(self):
        self.processed_events += 1


class FakeLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, message):
        self.warnings.append(message)


class FakeProgressDialog:
    instances = []

    def __init__(self, parent=None):
        self.parent = parent
        self.shown = False
        self.closed = False
        self.progress_values = []
        self.installing = False
        self.cancelled = False
        type(self).instances.append(self)

    def show(self):
        self.shown = True

    def close(self):
        self.closed = True

    def set_progress(self, value):
        self.progress_values.append(value)

    def was_cancelled(self):
        return self.cancelled

    def mark_installing(self):
        self.installing = True


class StartupAppUpdateTests(unittest.TestCase):
    def setUp(self):
        FakeProgressDialog.instances = []

    def test_download_app_update_uses_styled_progress_dialog(self):
        app = FakeApplication()
        logger = FakeLogger()
        parent = object()

        def download_update(url, progress_callback, expected_digest):
            self.assertEqual(expected_digest, "sha256:" + "a" * 64)
            progress_callback(42)
            return "setup.exe"

        result = download_app_update(
            "https://example.test/setup.exe",
            download_update,
            app,
            logger,
            progress_dialog_factory=FakeProgressDialog,
            parent=parent,
            expected_digest="sha256:" + "a" * 64,
        )

        self.assertEqual(result, "setup.exe")
        dialog = FakeProgressDialog.instances[0]
        self.assertIs(dialog.parent, parent)
        self.assertTrue(dialog.shown)
        self.assertTrue(dialog.closed)
        self.assertEqual(dialog.progress_values, [42])
        self.assertTrue(dialog.installing)
        self.assertEqual(logger.warnings, [])
        self.assertGreaterEqual(app.processed_events, 1)

    def test_download_app_update_returns_none_when_cancelled(self):
        app = FakeApplication()
        logger = FakeLogger()

        def download_update(url, progress_callback, expected_digest):
            dialog = FakeProgressDialog.instances[0]
            dialog.cancelled = True
            progress_callback(10)
            return "setup.exe"

        result = download_app_update(
            "https://example.test/setup.exe",
            download_update,
            app,
            logger,
            progress_dialog_factory=FakeProgressDialog,
            expected_digest="sha256:" + "a" * 64,
        )

        self.assertIsNone(result)
        self.assertTrue(FakeProgressDialog.instances[0].closed)
        self.assertEqual(FakeProgressDialog.instances[0].progress_values, [10])
        self.assertEqual(len(logger.warnings), 1)


if __name__ == "__main__":
    unittest.main()
