"""Stable task-workspace identities and persisted-data migration."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping
from uuid import uuid4


WORKSPACE_ID_LENGTH = 32
WORKSPACE_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
WORKSPACE_ID_SETTING = "_workspace_id"
LEGACY_WORKSPACE_SETTING = "_legacy_workspace_identity"


@dataclass(frozen=True)
class PersistedWorkspaceIdentity:
    """Workspace identity restored from one persisted task."""

    workspace_id: str
    legacy_workspace: bool


def new_workspace_id() -> str:
    """Return a unique, filesystem-safe UUID for one task workspace."""
    return uuid4().hex


def is_workspace_id(value: object) -> bool:
    """Return whether *value* is a canonical persisted workspace UUID."""
    return bool(WORKSPACE_ID_PATTERN.fullmatch(str(value or "")))


def restore_workspace_identity(
    task_data: Mapping[str, Any],
) -> PersistedWorkspaceIdentity:
    """
    Restore a task workspace ID, assigning one to pre-workspace-ID tasks.

    The legacy flag is persisted until the task is removed so a paused task
    can still discover deterministic temporary directories from older builds.
    """
    persisted_id = str(task_data.get("workspace_id") or "")
    if is_workspace_id(persisted_id):
        return PersistedWorkspaceIdentity(
            persisted_id,
            task_data.get("legacy_workspace") is True,
        )
    return PersistedWorkspaceIdentity(new_workspace_id(), True)
