import json
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

from core.ytdlp.info_parser import parse_info_output


class YtDlpInfoParserTests(unittest.TestCase):
    def test_single_json_object_returns_info(self):
        info, success = parse_info_output('{"id": "video-1", "title": "One"}')

        self.assertTrue(success)
        self.assertEqual(info["id"], "video-1")

    def test_multiple_json_lines_return_playlist_shape(self):
        stdout = "\n".join(
            [
                '{"id": "video-1"}',
                '{"id": "video-2"}',
            ]
        )

        info, success = parse_info_output(stdout)

        self.assertTrue(success)
        self.assertEqual(info["_type"], "playlist")
        self.assertEqual([entry["id"] for entry in info["entries"]], ["video-1", "video-2"])

    def test_mixed_multiline_output_skips_invalid_lines(self):
        stdout = "\n".join(
            [
                "not json",
                '{"id": "video-1"}',
                "",
            ]
        )

        info, success = parse_info_output(stdout)

        self.assertTrue(success)
        self.assertEqual(info, {"id": "video-1"})

    def test_blank_stdout_returns_failure(self):
        info, success = parse_info_output("  \n")

        self.assertFalse(success)
        self.assertIsNone(info)

    def test_invalid_single_json_line_raises_decode_error(self):
        with self.assertRaises(json.JSONDecodeError):
            parse_info_output("not json")


if __name__ == "__main__":
    unittest.main()
