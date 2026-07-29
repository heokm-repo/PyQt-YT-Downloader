import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.temp_workspace import task_temp_path, task_workspace_path
from core.download.workspace_cleanup import (
    build_workspace_cleanup_request,
    discard_task_workspace,
    remove_task_workspace,
    remove_workspace_cleanup_request,
)
from core.download.workspace_identity import new_workspace_id
from core.download.workspace_state import read_ready_source, write_ready_source
from core.download.workspace_state import destination_changed_since_ready


class WorkspaceStateTests(unittest.TestCase):
    def test_ready_source_round_trip_uses_relative_verified_path(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(
                task_temp_path(directory, "youtube", "abc", "mp4")
            )
            workspace.mkdir(parents=True)
            source = workspace / "title.mp4"
            source.write_bytes(b"media")

            write_ready_source(
                str(workspace),
                str(source),
                "title.mp4",
                136_515,
            )
            restored = read_ready_source(str(workspace))

            self.assertIsNotNone(restored)
            self.assertEqual(restored.source_path, str(source.resolve()))
            self.assertEqual(restored.final_name, "title.mp4")
            self.assertEqual(restored.audio_bitrate, 136_515)

    def test_ready_source_rejects_file_outside_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(
                task_temp_path(directory, "youtube", "abc", "mp4")
            )
            workspace.mkdir(parents=True)
            outside = Path(directory, "outside.mp4")
            outside.write_bytes(b"media")

            with self.assertRaises(ValueError):
                write_ready_source(
                    str(workspace),
                    str(outside),
                    "outside.mp4",
                )

    def test_ready_marker_keeps_final_name_after_source_was_moved(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(
                task_temp_path(directory, "youtube", "abc", "mp4")
            )
            workspace.mkdir(parents=True)
            source = workspace / "title.mp4"
            source.write_bytes(b"media")
            write_ready_source(str(workspace), str(source), "title.mp4")
            source.unlink()

            restored = read_ready_source(str(workspace))

            self.assertIsNotNone(restored)
            self.assertEqual(restored.final_name, "title.mp4")

    def test_existing_destination_is_not_mistaken_for_new_completion(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(
                task_temp_path(directory, "youtube", "abc", "mp4")
            )
            workspace.mkdir(parents=True)
            source = workspace / "title.mp4"
            destination = Path(directory, "title.mp4")
            source.write_bytes(b"new source")
            destination.write_bytes(b"old output")
            ready = write_ready_source(
                str(workspace),
                str(source),
                "title.mp4",
                destination_path=str(destination),
            )

            self.assertFalse(
                destination_changed_since_ready(ready, str(destination))
            )
            destination.write_bytes(b"new finalized output")
            self.assertTrue(
                destination_changed_since_ready(ready, str(destination))
            )

    def test_cleanup_removes_only_selected_hash_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            first = Path(task_temp_path(directory, "youtube", "one", "mp4"))
            second = Path(task_temp_path(directory, "youtube", "two", "mp4"))
            first.mkdir(parents=True)
            second.mkdir(parents=True)

            self.assertTrue(
                discard_task_workspace(directory, "youtube", "one", "mp4")
            )
            self.assertFalse(first.exists())
            self.assertTrue(second.exists())

    def test_cleanup_refuses_shared_temp_root(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_root = Path(directory, ".ytdl_temp")
            temp_root.mkdir()

            self.assertFalse(remove_task_workspace(str(temp_root)))
            self.assertTrue(temp_root.exists())

    def test_captured_uuid_cleanup_never_removes_same_media_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            removed_workspace_id = new_workspace_id()
            replacement_workspace_id = new_workspace_id()
            removed_workspace = Path(
                task_workspace_path(directory, removed_workspace_id)
            )
            replacement_workspace = Path(
                task_workspace_path(directory, replacement_workspace_id)
            )
            removed_workspace.mkdir(parents=True)
            replacement_workspace.mkdir(parents=True)
            request = build_workspace_cleanup_request(
                directory,
                removed_workspace_id,
            )

            self.assertTrue(remove_workspace_cleanup_request(request))
            self.assertFalse(removed_workspace.exists())
            self.assertTrue(replacement_workspace.exists())


if __name__ == "__main__":
    unittest.main()
