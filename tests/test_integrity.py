import hashlib
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
TEST_APPDATA = os.path.join(ROOT, "tests", ".appdata")
os.makedirs(TEST_APPDATA, exist_ok=True)
os.environ["APPDATA"] = TEST_APPDATA
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from utils.integrity import normalize_sha256_digest, verify_sha256


class IntegrityTests(unittest.TestCase):
    def test_normalize_sha256_digest_accepts_github_format(self):
        digest = "a" * 64
        self.assertEqual(normalize_sha256_digest(f"sha256:{digest}"), digest)
        self.assertIsNone(normalize_sha256_digest("sha1:" + "a" * 40))
        self.assertIsNone(normalize_sha256_digest(None))

    def test_verify_sha256_accepts_match_and_rejects_mismatch_or_missing_digest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "artifact.bin"
            file_path.write_bytes(b"trusted artifact")
            digest = hashlib.sha256(b"trusted artifact").hexdigest()

            self.assertTrue(verify_sha256(str(file_path), f"sha256:{digest}"))
            self.assertFalse(verify_sha256(str(file_path), "sha256:" + "0" * 64))
            self.assertFalse(verify_sha256(str(file_path), None))


if __name__ == "__main__":
    unittest.main()
