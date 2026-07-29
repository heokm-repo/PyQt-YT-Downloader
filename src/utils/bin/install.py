"""Install helpers for managed binary downloads."""

import os
import shutil
from typing import Any, Callable, Mapping


def version_record(
    versions: Mapping[str, Any],
    binary_name: str,
    version: str,
) -> dict[str, Any]:
    """Return versions updated with one managed binary version."""
    updated = dict(versions)
    updated.pop("last_check", None)
    updated[binary_name] = version
    return updated


def remove_if_exists(path: str) -> bool:
    """Remove a file when it exists and return whether it was removed."""
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True


def replace_existing_file(source_path: str, final_path: str) -> None:
    """Replace final_path with source_path."""
    remove_if_exists(final_path)
    shutil.move(source_path, final_path)


def save_binary_version(
    binary_name: str,
    version: str,
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
) -> bool:
    """Persist a binary version update."""
    return save_versions(version_record(load_versions(), binary_name, version))


def install_downloaded_binary(
    temp_path: str,
    final_path: str,
    binary_name: str,
    version: str,
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
) -> bool:
    """Move a downloaded temp binary into place and persist its version."""
    replace_existing_file(temp_path, final_path)
    return save_binary_version(binary_name, version, load_versions, save_versions)
