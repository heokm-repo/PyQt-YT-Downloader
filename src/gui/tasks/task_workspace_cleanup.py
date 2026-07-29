"""Capture cleanup requests from task data before GUI removal."""

from __future__ import annotations

from typing import Any

from constants import DEFAULT_FORMAT
from core.download.workspace_cleanup import (
    WorkspaceCleanupRequest,
    build_workspace_cleanup_request,
)
from core.download.workspace_identity import is_workspace_id
from utils.settings_store import get_download_folder


def build_task_cleanup_request(task: Any) -> WorkspaceCleanupRequest:
    """Return immutable UUID and legacy paths belonging to one task."""
    settings = getattr(task, "settings", None) or {}
    workspace_id = getattr(task, "workspace_id", "")
    legacy_identity = None
    if getattr(
        task,
        "legacy_workspace",
        not is_workspace_id(workspace_id),
    ):
        legacy_identity = {
            "extractor": getattr(task, "extractor", "unknown"),
            "video_id": getattr(task, "video_id", None),
            "url": getattr(task, "url", ""),
            "format": settings.get("format", DEFAULT_FORMAT),
        }
    return build_workspace_cleanup_request(
        get_download_folder(settings),
        workspace_id,
        legacy_identity=legacy_identity,
    )
