import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils import download_stream


class FakeResponse:
    def __init__(self, chunks, total_size=0):
        self.chunks = chunks
        self.headers = {"content-length": str(total_size)}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        return iter(self.chunks)


class DownloadStreamTests(unittest.TestCase):
    def test_download_file_writes_chunks_and_reports_progress(self):
        progress = []
        response = FakeResponse([b"abc", b"", b"def"], total_size=6)

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(download_stream.requests, "get", return_value=response) as request_get:
            dest_path = Path(tmpdir) / "tool.exe"

            result = download_stream.download_file(
                "https://example.test/tool.exe",
                str(dest_path),
                lambda downloaded, total: progress.append((downloaded, total)),
            )

            self.assertTrue(result)
            self.assertEqual(dest_path.read_bytes(), b"abcdef")

        request_get.assert_called_once_with("https://example.test/tool.exe", stream=True, timeout=30)
        self.assertEqual(progress, [(3, 6), (6, 6)])

    def test_download_file_cancellation_removes_partial_file(self):
        response = FakeResponse([b"abc", b"def"], total_size=6)
        cancel_results = iter([False, False, True])

        with tempfile.TemporaryDirectory() as tmpdir, \
                patch.object(download_stream.requests, "get", return_value=response):
            dest_path = Path(tmpdir) / "tool.exe"

            result = download_stream.download_file(
                "https://example.test/tool.exe",
                str(dest_path),
                check_cancel=lambda: next(cancel_results),
            )

            self.assertFalse(result)
            self.assertFalse(dest_path.exists())


if __name__ == "__main__":
    unittest.main()