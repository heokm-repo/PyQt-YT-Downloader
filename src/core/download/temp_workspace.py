"""Temporary workspace path primitives for current and legacy tasks."""

from hashlib import sha256
import os

from constants import YTDL_TEMP_DIR
from core.download.workspace_identity import is_workspace_id


TEMP_WORKSPACE_ID_LENGTH = 16


def temp_workspace_id(
    extractor: object,
    video_id: object,
    output_format: object,
) -> str:
    """Return the deterministic ID used by releases before task UUIDs."""
    identity = "\0".join(
        str(value or "").strip().lower()
        for value in (extractor, video_id, output_format)
    )
    return sha256(identity.encode("utf-8")).hexdigest()[
        :TEMP_WORKSPACE_ID_LENGTH
    ]


legacy_temp_workspace_id = temp_workspace_id


def task_temp_path(
    save_path: str,
    extractor: object,
    video_id: object,
    output_format: object,
) -> str:
    """Return a legacy deterministic task directory below the temp root."""
    return os.path.join(
        save_path,
        YTDL_TEMP_DIR,
        temp_workspace_id(extractor, video_id, output_format),
    )


def task_workspace_path(save_path: str, workspace_id: object) -> str:
    """Return the unique workspace path for a current task UUID."""
    if not is_workspace_id(workspace_id):
        raise ValueError("Invalid task workspace ID")
    return os.path.join(save_path, YTDL_TEMP_DIR, str(workspace_id))
