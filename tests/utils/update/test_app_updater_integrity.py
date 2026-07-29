import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils import app_updater


class FakeResponse:
    def __init__(self, *, data=None, chunks=()):
        self._data = data
        self._chunks = chunks
        self.headers = {"content-length": str(sum(len(chunk) for chunk in chunks))}

    def raise_for_status(self):
        return None

    def json(self):
        return self._data

    def iter_content(self, chunk_size):
        return iter(self._chunks)


class AppUpdaterIntegrityTests(unittest.TestCase):
    def test_check_for_updates_returns_release_asset_digest(self):
        digest = "sha256:" + "a" * 64
        response = FakeResponse(data={
            "tag_name": "v9.9.9",
            "assets": [{
                "name": "setup-YTDownloader.exe",
                "browser_download_url": "https://example.test/setup.exe",
                "digest": digest,
            }],
        })

        with patch.object(app_updater.requests, "get", return_value=response), patch.object(
            app_updater,
            "APP_VERSION",
            "1.0.0",
        ):
            result = app_updater.check_for_updates()

        self.assertEqual(
            result,
            (True, "9.9.9", "https://example.test/setup.exe", digest),
        )

    def test_download_update_returns_only_verified_installer(self):
        content = b"verified setup"
        digest = "sha256:" + hashlib.sha256(content).hexdigest()
        response = FakeResponse(chunks=(content,))

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            app_updater,
            "update_temp_dir",
            return_value=tmpdir,
        ), patch.object(app_updater.requests, "get", return_value=response):
            result = app_updater.download_update(
                "https://example.test/setup.exe?token=secret",
                expected_digest=digest,
            )

            self.assertEqual(Path(result).read_bytes(), content)

    def test_download_update_deletes_digest_mismatch(self):
        response = FakeResponse(chunks=(b"tampered",))

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            app_updater,
            "update_temp_dir",
            return_value=tmpdir,
        ), patch.object(app_updater.requests, "get", return_value=response):
            result = app_updater.download_update(
                "https://example.test/setup.exe",
                expected_digest="sha256:" + "0" * 64,
            )

            self.assertIsNone(result)
            self.assertFalse(Path(tmpdir, app_updater.UPDATE_TEMP_FILENAME).exists())

    def test_download_update_deletes_partial_file_when_cancelled(self):
        content = b"partial setup"
        response = FakeResponse(chunks=(content,))

        def cancel(_percent):
            raise RuntimeError("Cancelled by user")

        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            app_updater,
            "update_temp_dir",
            return_value=tmpdir,
        ), patch.object(app_updater.requests, "get", return_value=response):
            result = app_updater.download_update(
                "https://example.test/setup.exe",
                progress_callback=cancel,
                expected_digest="sha256:" + hashlib.sha256(content).hexdigest(),
            )

            self.assertIsNone(result)
            self.assertFalse(Path(tmpdir, app_updater.UPDATE_TEMP_FILENAME).exists())

    def test_strict_update_check_surfaces_network_failure(self):
        with patch.object(
            app_updater.requests,
            "get",
            side_effect=app_updater.requests.RequestException("network down"),
        ), self.assertRaises(app_updater.AppUpdateCheckError):
            app_updater.check_for_updates_strict()

    def test_strict_update_check_rejects_asset_without_digest(self):
        response = FakeResponse(data={
            "tag_name": "v9.9.9",
            "assets": [{
                "name": "setup-YTDownloader.exe",
                "browser_download_url": "https://example.test/setup.exe",
            }],
        })

        with patch.object(
            app_updater.requests,
            "get",
            return_value=response,
        ), patch.object(
            app_updater,
            "APP_VERSION",
            "1.0.0",
        ), self.assertRaises(app_updater.AppUpdateCheckError):
            app_updater.check_for_updates_strict()


if __name__ == "__main__":
    unittest.main()
