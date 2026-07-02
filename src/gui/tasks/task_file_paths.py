"""Path resolution helpers for task file actions."""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FolderOpenTarget:
    path: str
    select_file: bool = False


def normalize_output_path(path: str) -> str:
    """Return an absolute output path, or an empty string for missing paths."""
    if not path:
        return ""
    if os.path.isabs(path):
        return path
    return os.path.abspath(path)


def existing_file_path(path: str) -> str:
    """Return an absolute path when it exists and is a file, else empty string."""
    normalized_path = normalize_output_path(path)
    if normalized_path and os.path.exists(normalized_path) and os.path.isfile(normalized_path):
        return normalized_path
    return ""


def resolve_open_folder_target(output_path: str) -> Optional[FolderOpenTarget]:
    """Return the best folder-open target for a task output path."""
    normalized_path = normalize_output_path(output_path)
    if not normalized_path:
        return None

    if os.path.exists(normalized_path):
        return FolderOpenTarget(normalized_path, select_file=True)

    folder = os.path.dirname(normalized_path)
    if folder and os.path.exists(folder):
        return FolderOpenTarget(folder, select_file=False)

    return None


def existing_parent_folder(output_path: str) -> str:
    """Return an existing parent folder for an output path, or empty string."""
    normalized_path = normalize_output_path(output_path)
    if not normalized_path:
        return ""

    folder = os.path.dirname(normalized_path)
    if folder and os.path.exists(folder):
        return folder
    return ""
