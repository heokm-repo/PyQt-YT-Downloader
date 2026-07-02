import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download import handler as download_handler


class DownloadHandlerFacadeTests(unittest.TestCase):
    def test_download_handler_exports_only_public_worker_api(self):
        self.assertEqual(
            download_handler.__all__,
            (
                "download_video",
                "fetch_metadata",
                "extract_playlist_video_ids",
            ),
        )
        self.assertFalse(hasattr(download_handler, "_build_all_options"))
        self.assertFalse(hasattr(download_handler, "_build_format_options"))

    def test_youtube_handler_compatibility_module_is_removed(self):
        self.assertFalse(os.path.exists(os.path.join(SRC, "core", "youtube_handler.py")))


if __name__ == "__main__":
    unittest.main()
