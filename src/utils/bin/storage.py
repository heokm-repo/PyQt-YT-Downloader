"""Storage helpers for managed binary paths and version metadata."""

import json
import os
from typing import Any, Mapping

from utils.logger import log
from utils.utils import get_user_data_path


def get_bin_path() -> str:
    """Return the directory used for managed binary files."""
    bin_path = os.path.join(get_user_data_path(), 'bin')

    if not os.path.exists(bin_path):
        try:
            os.makedirs(bin_path, exist_ok=True)
            log.info(f"Created bin directory: {bin_path}")
        except OSError as e:
            log.error(f"Failed to create bin directory: {e}")
            raise

    return bin_path


def binary_path(binary_name: str) -> str | None:
    """Return a managed binary path when the file exists."""
    path = os.path.join(get_bin_path(), binary_name)
    return path if os.path.exists(path) else None


def version_file_path(version_file: str) -> str:
    """Return the managed binary version metadata file path."""
    return os.path.join(get_bin_path(), version_file)


def load_versions_file(version_file: str) -> dict[str, Any]:
    """Load managed binary version metadata."""
    path = version_file_path(version_file)

    if not os.path.exists(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            versions = json.load(f)
        if not isinstance(versions, dict):
            return {}
        if "last_check" in versions:
            versions.pop("last_check")
            save_versions_file(versions, version_file)
        return versions
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Failed to load version file: {e}")
        return {}


def save_versions_file(versions: Mapping[str, Any], version_file: str) -> bool:
    """Persist managed binary version metadata."""
    path = version_file_path(version_file)

    try:
        version_data = dict(versions)
        version_data.pop("last_check", None)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        log.error(f"Failed to save version file: {e}")
        return False
