"""Shared path helpers for downloaded media files and task file actions."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Optional

from constants import YTDL_TEMP_DIR


@dataclass(frozen=True)
class FolderOpenTarget:
    path: str
    select_file: bool = False


def normalize_output_path(path: str, base_directory: str | None = None) -> str:
    """Return an absolute output path, or an empty string for missing paths."""
    if not path:
        return ""
    if os.path.isabs(path):
        return os.path.abspath(path)
    if base_directory:
        return os.path.abspath(os.path.join(base_directory, path))
    return os.path.abspath(path)


def existing_file_path(path: str, base_directory: str | None = None) -> str:
    """Return an absolute path when it exists and is a file, else empty string."""
    normalized_path = normalize_output_path(path, base_directory)
    if normalized_path and os.path.exists(normalized_path) and os.path.isfile(normalized_path):
        return normalized_path
    return ""


def verified_download_output_path(path: str, download_folder: str) -> str:
    """
    Return a trusted completed-download path.

    Destructive post-processing must only receive an existing file inside the
    configured download folder and outside yt-dlp's temporary directory.
    """
    file_path = existing_file_path(path, download_folder)
    if not file_path or not download_folder:
        return ""

    try:
        resolved_file = Path(file_path).resolve(strict=True)
        resolved_root = Path(download_folder).resolve(strict=True)
        resolved_file.relative_to(resolved_root)
    except (OSError, RuntimeError, ValueError):
        return ""

    try:
        resolved_file.relative_to((resolved_root / YTDL_TEMP_DIR).resolve())
    except ValueError:
        return str(resolved_file)
    return ""


def verified_workspace_output_path(path: str, workspace: str) -> str:
    """Return an existing file only when it is inside the exact task workspace."""
    file_path = existing_file_path(path, workspace)
    if not file_path or not workspace:
        return ""
    try:
        resolved_file = Path(file_path).resolve(strict=True)
        resolved_workspace = Path(workspace).resolve(strict=True)
        resolved_file.relative_to(resolved_workspace)
        return str(resolved_file)
    except (OSError, RuntimeError, ValueError):
        return ""


def resolve_open_folder_target(output_path: str) -> Optional[FolderOpenTarget]:
    """Return the best folder-open target for a task output path."""
    normalized_path = normalize_output_path(output_path)
    if not normalized_path:
        return None

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
