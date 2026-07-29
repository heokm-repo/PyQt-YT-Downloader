import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.options import _build_all_options
from core.download.temp_workspace import (
    task_temp_path,
    task_workspace_path,
    temp_workspace_id,
)
from core.download.workspace_identity import new_workspace_id


class TempWorkspaceTests(unittest.TestCase):
    def test_workspace_id_is_stable_and_does_not_expose_media_id(self):
        first = temp_workspace_id("youtube", "secret-id", "mp4")

        self.assertEqual(
            first,
            temp_workspace_id("youtube", "secret-id", "mp4"),
        )
        self.assertEqual(len(first), 16)
        self.assertNotIn("secret-id", first)

    def test_three_history_identities_receive_three_task_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            identities = [
                {"extractor": "youtube", "id": "one"},
                {"extractor": "youtube", "id": "two"},
                {"extractor": "youtube", "id": "three"},
            ]
            paths = {
                _build_all_options(
                    {"format": "mp4"},
                    directory,
                    "ffmpeg.exe",
                    False,
                    url=f"https://example.invalid/{identity['id']}",
                    temp_identity=identity,
                )["temp_path"]
                for identity in identities
            }

            self.assertEqual(len(paths), 3)
            self.assertTrue(all(Path(path).is_dir() for path in paths))
            self.assertTrue(
                all(Path(path).parent.name == ".ytdl_temp" for path in paths)
            )

    def test_mp4_and_mp3_use_different_workspaces(self):
        mp4 = temp_workspace_id("youtube", "abc", "mp4")
        mp3 = temp_workspace_id("youtube", "abc", "mp3")

        self.assertNotEqual(mp4, mp3)

    def test_quality_does_not_change_the_three_field_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            first = _build_all_options(
                {"format": "mp4", "video_quality": "1080p"},
                directory,
                "ffmpeg.exe",
                False,
                temp_identity={"extractor": "youtube", "id": "abc"},
            )["temp_path"]
            second = _build_all_options(
                {"format": "mp4", "video_quality": "720p"},
                directory,
                "ffmpeg.exe",
                False,
                temp_identity={"extractor": "youtube", "id": "abc"},
            )["temp_path"]

        self.assertEqual(first, second)

    def test_task_temp_path_is_below_shared_temp_root(self):
        path = Path(task_temp_path("C:/Downloads", "youtube", "abc", "mp4"))

        self.assertEqual(path.parent.name, ".ytdl_temp")

    def test_current_options_use_exact_unique_task_workspace_uuid(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace_id = new_workspace_id()

            options = _build_all_options(
                {"format": "mp4"},
                directory,
                "ffmpeg.exe",
                False,
                temp_identity={
                    "workspace_id": workspace_id,
                    "extractor": "Example",
                    "id": "CaseSensitive-ID",
                },
            )

            self.assertEqual(
                options["temp_path"],
                task_workspace_path(directory, workspace_id),
            )
