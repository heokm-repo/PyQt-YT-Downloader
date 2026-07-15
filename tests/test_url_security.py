import logging
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.logger import RedactingFormatter
from utils.url_security import redact_url_for_log, redact_urls_in_text


class UrlSecurityTests(unittest.TestCase):
    def test_redact_url_for_log_removes_query_fragment_and_credentials(self):
        self.assertEqual(
            redact_url_for_log(
                "https://user:secret@example.test/video?id=123&token=secret#part"
            ),
            "https://example.test/video",
        )

    def test_redact_urls_in_text_redacts_each_embedded_url(self):
        message = (
            "failed https://example.test/a?token=one and "
            "https://other.test/b?id=two#fragment"
        )
        self.assertEqual(
            redact_urls_in_text(message),
            "failed https://example.test/a and https://other.test/b",
        )

    def test_logging_formatter_redacts_urls_from_exception_traceback(self):
        formatter = RedactingFormatter("%(message)s")
        try:
            raise RuntimeError("request failed: https://example.test/a?token=secret")
        except RuntimeError:
            record = logging.LogRecord(
                "test",
                logging.ERROR,
                __file__,
                1,
                "download failed",
                (),
                sys.exc_info(),
            )

        rendered = formatter.format(record)
        self.assertIn("https://example.test/a", rendered)
        self.assertNotIn("token=secret", rendered)


if __name__ == "__main__":
    unittest.main()
