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

from utils import cookie_store
from utils.cookie_store import is_youtube_cookie_domain


class CookieStoreTests(unittest.TestCase):
    def test_youtube_cookie_domain_uses_domain_boundaries(self):
        self.assertTrue(is_youtube_cookie_domain("youtube.com"))
        self.assertTrue(is_youtube_cookie_domain(".youtube.com"))
        self.assertTrue(is_youtube_cookie_domain(".music.youtube.com"))
        self.assertFalse(is_youtube_cookie_domain("youtube.com.example.test"))
        self.assertFalse(is_youtube_cookie_domain("notyoutube.com"))

    def test_delete_stored_login_data_removes_cookie_and_webengine_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir, patch.object(
            cookie_store,
            "get_user_data_path",
            return_value=tmpdir,
        ):
            Path(tmpdir, cookie_store.COOKIE_FILENAME).write_text("cookie", encoding="utf-8")
            for folder in (
                cookie_store.WEBENGINE_CACHE_DIR,
                cookie_store.WEBENGINE_STORAGE_DIR,
            ):
                Path(tmpdir, folder).mkdir()
                Path(tmpdir, folder, "state").write_text("data", encoding="utf-8")

            self.assertTrue(cookie_store.delete_stored_login_data())

            self.assertFalse(Path(tmpdir, cookie_store.COOKIE_FILENAME).exists())
            self.assertFalse(Path(tmpdir, cookie_store.WEBENGINE_CACHE_DIR).exists())
            self.assertFalse(Path(tmpdir, cookie_store.WEBENGINE_STORAGE_DIR).exists())


if __name__ == "__main__":
    unittest.main()
