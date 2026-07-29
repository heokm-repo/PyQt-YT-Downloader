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

from gui.tasks.task_thumbnail_request import THUMBNAIL_USER_AGENT, build_thumbnail_request


class TaskThumbnailRequestTests(unittest.TestCase):
    def test_build_thumbnail_request_sets_url_and_user_agent(self):
        request = build_thumbnail_request("https://example.invalid/thumb.jpg")

        self.assertEqual(request.url().toString(), "https://example.invalid/thumb.jpg")
        self.assertEqual(bytes(request.rawHeader(b"User-Agent")), THUMBNAIL_USER_AGENT)


if __name__ == "__main__":
    unittest.main()