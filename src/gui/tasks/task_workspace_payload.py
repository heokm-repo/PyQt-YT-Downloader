"""Build immutable scheduler payloads for task workspace lifecycle."""

from __future__ import annotations

from typing import Any, Mapping

from constants import DEFAULT_FORMAT
from core.download.workspace_identity import (
    LEGACY_WORKSPACE_SETTING,
    WORKSPACE_ID_SETTING,
    is_workspace_id,
)


def build_workspace_execution_settings(
    task: Any,
    settings: Mapping[str, Any],
    *,
    resume: bool,
) -> dict:
    """Copy settings and attach the task's stable workspace identity."""
    execution_settings = dict(settings)
    workspace_id = getattr(task, "workspace_id", "")
    if not is_workspace_id(workspace_id):
        execution_settings.pop(WORKSPACE_ID_SETTING, None)
        execution_settings.pop(LEGACY_WORKSPACE_SETTING, None)
        return execution_settings
    execution_settings[WORKSPACE_ID_SETTING] = workspace_id

    if resume and getattr(task, "legacy_workspace", False):
        execution_settings[LEGACY_WORKSPACE_SETTING] = {
            "extractor": getattr(task, "extractor", "unknown"),
            "video_id": getattr(task, "video_id", None),
            "url": getattr(task, "url", ""),
            "format": execution_settings.get("format", DEFAULT_FORMAT),
        }
    else:
        execution_settings.pop(LEGACY_WORKSPACE_SETTING, None)
    return execution_settings
