import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from core.download.temp_workspace import task_temp_path, task_workspace_path
from core.download.workspace_identity import new_workspace_id
from core.download.workspace_migration import (
    WorkspaceMigrationError,
    prepare_task_workspace,
)


class WorkspaceMigrationTests(unittest.TestCase):
    def test_migrates_actual_extractor_and_media_id_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(
                task_temp_path(tmpdir, "Vimeo", "CaseSensitive-ID", "mp4")
            )
            legacy.mkdir(parents=True)
            (legacy / "video.part").write_text("partial", encoding="utf-8")
            workspace_id = new_workspace_id()

            result = prepare_task_workspace(
                tmpdir,
                workspace_id,
                migrate_legacy=True,
                legacy_identity={
                    "extractor": "Vimeo",
                    "video_id": "CaseSensitive-ID",
                    "url": "https://vimeo.test/CaseSensitive-ID",
                    "format": "mp4",
                },
            )

            target = Path(task_workspace_path(tmpdir, workspace_id))
            self.assertEqual(Path(result.workspace_path), target)
            self.assertEqual(Path(result.migrated_from), legacy)
            self.assertFalse(legacy.exists())
            self.assertEqual(
                (target / "video.part").read_text(encoding="utf-8"),
                "partial",
            )

    def test_migrates_initial_unknown_url_workspace_without_metadata(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            url = "https://media.example/Watch/ABC"
            legacy = Path(task_temp_path(tmpdir, "unknown", url, "webm"))
            legacy.mkdir(parents=True)
            (legacy / "fragment.part").write_text("partial", encoding="utf-8")
            workspace_id = new_workspace_id()

            result = prepare_task_workspace(
                tmpdir,
                workspace_id,
                migrate_legacy=True,
                legacy_identity={
                    "extractor": "unknown",
                    "video_id": None,
                    "url": url,
                    "format": "webm",
                },
            )

            self.assertEqual(Path(result.migrated_from), legacy)
            self.assertTrue(
                (Path(result.workspace_path) / "fragment.part").is_file()
            )

    def test_empty_uuid_target_retries_legacy_migration(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(task_temp_path(tmpdir, "youtube", "abc", "mp4"))
            legacy.mkdir(parents=True)
            (legacy / "fragment.part").write_text("partial", encoding="utf-8")
            workspace_id = new_workspace_id()
            target = Path(task_workspace_path(tmpdir, workspace_id))
            target.mkdir(parents=True)

            result = prepare_task_workspace(
                tmpdir,
                workspace_id,
                migrate_legacy=True,
                legacy_identity={
                    "extractor": "youtube",
                    "video_id": "abc",
                    "url": "https://www.youtube.com/watch?v=abc",
                    "format": "mp4",
                },
            )

            self.assertEqual(Path(result.migrated_from), legacy)
            self.assertTrue((target / "fragment.part").is_file())

    def test_failed_rename_does_not_leave_empty_target_or_start_fresh(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            legacy = Path(task_temp_path(tmpdir, "youtube", "abc", "mp4"))
            legacy.mkdir(parents=True)
            (legacy / "fragment.part").write_text("partial", encoding="utf-8")
            workspace_id = new_workspace_id()
            target = Path(task_workspace_path(tmpdir, workspace_id))
            identity = {
                "extractor": "youtube",
                "video_id": "abc",
                "url": "https://www.youtube.com/watch?v=abc",
                "format": "mp4",
            }

            with patch.object(
                Path,
                "rename",
                side_effect=PermissionError("workspace is locked"),
            ):
                with self.assertRaises(WorkspaceMigrationError):
                    prepare_task_workspace(
                        tmpdir,
                        workspace_id,
                        migrate_legacy=True,
                        legacy_identity=identity,
                    )

            self.assertFalse(target.exists())
            self.assertTrue((legacy / "fragment.part").is_file())

            result = prepare_task_workspace(
                tmpdir,
                workspace_id,
                migrate_legacy=True,
                legacy_identity=identity,
            )
            self.assertEqual(Path(result.migrated_from), legacy)
            self.assertTrue((target / "fragment.part").is_file())


if __name__ == "__main__":
    unittest.main()
