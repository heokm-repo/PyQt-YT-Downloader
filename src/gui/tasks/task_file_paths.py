"""Compatibility imports for shared downloaded-media path helpers."""

from core.download.output_paths import (
    FolderOpenTarget,
    existing_file_path,
    existing_parent_folder,
    normalize_output_path,
    resolve_open_folder_target,
)

__all__ = (
    "FolderOpenTarget",
    "existing_file_path",
    "existing_parent_folder",
    "normalize_output_path",
    "resolve_open_folder_target",
)
