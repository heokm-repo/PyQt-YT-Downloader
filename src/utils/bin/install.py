"""Install helpers for managed binary downloads."""

import os
import shutil
from datetime import datetime
from typing import Any, Callable, Mapping


def version_record_with_check(
    versions: Mapping[str, Any],
    binary_name: str,
    version: str,
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    """Return versions updated with a binary version and last_check timestamp."""
    updated = last_check_record(versions, checked_at)
    updated[binary_name] = version
    return updated


def last_check_record(
    versions: Mapping[str, Any],
    checked_at: datetime | None = None,
) -> dict[str, Any]:
    """Return versions updated with only the last_check timestamp."""
    updated = dict(versions)
    updated["last_check"] = (checked_at or datetime.now()).isoformat()
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
    checked_at: datetime | None = None,
) -> bool:
    """Persist a binary version update."""
    return save_versions(
        version_record_with_check(load_versions(), binary_name, version, checked_at)
    )


def save_last_check(
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
    checked_at: datetime | None = None,
) -> bool:
    """Persist only the last update-check timestamp."""
    return save_versions(last_check_record(load_versions(), checked_at))


def install_downloaded_binary(
    temp_path: str,
    final_path: str,
    binary_name: str,
    version: str,
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
    checked_at: datetime | None = None,
) -> bool:
    """Move a downloaded temp binary into place and persist its version."""
    replace_existing_file(temp_path, final_path)
    return save_binary_version(binary_name, version, load_versions, save_versions, checked_at)