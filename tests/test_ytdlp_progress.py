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

from core.ytdlp.progress import convert_to_bytes, parse_eta, parse_progress
from core.ytdlp.wrapper import YtDlpWrapper


class YtDlpProgressTests(unittest.TestCase):
    def test_parse_progress_with_speed_and_eta(self):
        progress = parse_progress("[download]  45.2% of 10.5MiB at 2.3MiB/s ETA 00:03")

        self.assertEqual(progress["status"], "downloading")
        self.assertEqual(progress["total_bytes"], 11010048)
        self.assertEqual(progress["downloaded_bytes"], 4976541)
        self.assertEqual(progress["speed"], 2411724)
        self.assertEqual(progress["eta"], 3)
        self.assertEqual(progress["_percent_str"], "45.2%")
        self.assertEqual(progress["_total_bytes_str"], "10.5MiB")
        self.assertEqual(progress["_speed_str"], "2.3MiB/s")

    def test_parse_progress_without_speed_or_eta(self):
        progress = parse_progress("[download]  12.0% of 100.0KB")

        self.assertEqual(progress["total_bytes"], 100000)
        self.assertEqual(progress["downloaded_bytes"], 12000)
        self.assertIsNone(progress["speed"])
        self.assertIsNone(progress["eta"])
        self.assertIsNone(progress["_speed_str"])

    def test_parse_progress_ignores_non_progress_line(self):
        self.assertIsNone(parse_progress("[download] Destination: file.mp4"))

    def test_convert_to_bytes_handles_binary_and_decimal_units(self):
        self.assertEqual(convert_to_bytes(1.5, "MiB"), 1572864)
        self.assertEqual(convert_to_bytes(1.5, "MB"), 1500000)
        self.assertEqual(convert_to_bytes(2, "GiB"), 2147483648)

    def test_parse_eta_handles_mmss_and_hhmmss(self):
        self.assertEqual(parse_eta("00:03"), 3)
        self.assertEqual(parse_eta("01:02:03"), 3723)
        self.assertEqual(parse_eta("bad"), 0)

    def test_wrapper_private_methods_delegate_to_parser(self):
        wrapper = YtDlpWrapper("yt-dlp.exe")

        self.assertEqual(wrapper._convert_to_bytes(1, "KiB"), 1024)
        self.assertEqual(wrapper._parse_eta("01:00"), 60)
        self.assertEqual(wrapper._parse_progress("[download]  50.0% of 2.0KiB")["downloaded_bytes"], 1024)


if __name__ == "__main__":
    unittest.main()
