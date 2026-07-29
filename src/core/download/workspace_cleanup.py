"""Safely remove captured task workspaces, never the shared temp root."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shutil
from typing import Any, Mapping

from constants import YTDL_TEMP_DIR
from core.download.temp_workspace import task_temp_path, task_workspace_path
from core.download.workspace_identity import is_workspace_id
from core.download.workspace_migration import legacy_workspace_paths
from utils.logger import log


WORKSPACE_NAME_PATTERN = re.compile(r"^(?:[0-9a-f]{16}|[0-9a-f]{32})$")


@dataclass(frozen=True)
class WorkspaceCleanupRequest:
    """Immutable paths captured before a task is removed from the model."""

    workspace_paths: tuple[str, ...]


def remove_task_workspace(workspace: str) -> bool:
    """Remove one validated hash workspace and optionally its empty parent."""
    if not workspace:
        return False
    candidate = Path(workspace)
    try:
        resolved = candidate.resolve()
        parent = resolved.parent
        if (
            parent.name != YTDL_TEMP_DIR
            or not WORKSPACE_NAME_PATTERN.fullmatch(resolved.name)
        ):
            log.warning("Refusing to remove untrusted task workspace: %s", workspace)
            return False
        if not resolved.exists():
            return True
        if not resolved.is_dir():
            return False
        shutil.rmtree(resolved)
        try:
            os.rmdir(parent)
        except OSError as exc:
            log.debug(
                "Task workspace parent remains in use %s: %s",
                parent,
                exc,
            )
        return True
    except OSError as exc:
        log.warning("Failed to remove task workspace %s: %s", workspace, exc)
        return False


def discard_task_workspace(
    save_path: str,
    extractor: object,
    video_id: object,
    output_format: object,
) -> bool:
    """Resolve and remove the exact workspace belonging to one task."""
    return remove_task_workspace(
        task_temp_path(save_path, extractor, video_id, output_format)
    )


def build_workspace_cleanup_request(
    save_path: str,
    workspace_id: object,
    *,
    legacy_identity: Mapping[str, Any] | None = None,
) -> WorkspaceCleanupRequest:
    """Capture the current UUID path and any explicit legacy candidates."""
    paths: list[str] = []
    if save_path and is_workspace_id(workspace_id):
        paths.append(task_workspace_path(save_path, workspace_id))
    if save_path and legacy_identity is not None:
        for legacy_path in legacy_workspace_paths(save_path, legacy_identity):
            if legacy_path not in paths:
                paths.append(legacy_path)
    return WorkspaceCleanupRequest(tuple(paths))


def remove_workspace_cleanup_request(
    request: WorkspaceCleanupRequest,
) -> bool:
    """Remove every path in a previously captured cleanup request."""
    removed = True
    for workspace_path in request.workspace_paths:
        removed = remove_task_workspace(workspace_path) and removed
    return removed
