import os
import sys
import unittest
from unittest.mock import patch

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.bin import release_fetch as bin_release_fetch


class FakeReleaseResponse:
    def __init__(self, data):
        self.data = data

    def raise_for_status(self):
        return None

    def json(self):
        return self.data


class BinReleaseFetchTests(unittest.TestCase):
    def test_check_latest_github_release_fetches_and_parses_release(self):
        response = FakeReleaseResponse({"tag_name": "v1"})

        with patch.object(bin_release_fetch.requests, "get", return_value=response) as request_get:
            result = bin_release_fetch.check_latest_github_release(
                "https://example.test/releases/latest",
                "tool",
                lambda data: (
                    data["tag_name"],
                    "https://example.test/tool.exe",
                    "sha256:" + "a" * 64,
                ),
                "missing",
            )

        self.assertEqual(
            result,
            ("v1", "https://example.test/tool.exe", "sha256:" + "a" * 64),
        )
        request_get.assert_called_once_with("https://example.test/releases/latest", timeout=10)

    def test_check_latest_github_release_returns_none_without_asset(self):
        response = FakeReleaseResponse({"tag_name": "v1"})

        with patch.object(bin_release_fetch.requests, "get", return_value=response):
            result = bin_release_fetch.check_latest_github_release(
                "https://example.test/releases/latest",
                "tool",
                lambda data: ("v1", None, None),
                "missing",
            )

        self.assertEqual(result, (None, None, None))

    def test_check_latest_github_release_returns_none_on_request_error(self):
        with patch.object(
            bin_release_fetch.requests,
            "get",
            side_effect=bin_release_fetch.requests.RequestException("network down"),
        ):
            result = bin_release_fetch.check_latest_github_release(
                "https://example.test/releases/latest",
                "tool",
                lambda data: ("v1", "url", "sha256:" + "a" * 64),
                "missing",
            )

        self.assertEqual(result, (None, None, None))


if __name__ == "__main__":
    unittest.main()
