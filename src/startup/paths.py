"""Startup path handling for source and frozen builds."""
from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from typing import MutableSequence


@dataclass(frozen=True)
class StartupPaths:
    application_path: str
    bundled_src_path: str | None = None


def add_sys_path(path: str, sys_path: MutableSequence[str] | None = None) -> bool:
    """Add a path to sys.path if it is not already present."""
    paths = sys.path if sys_path is None else sys_path
    if path and path not in paths:
        paths.insert(0, path)
        return True
    return False


def initialize_startup_paths(
    base_file: str,
    src_dir_name: str,
    frozen: bool | None = None,
    meipass: str | None = None,
    path_exists=os.path.exists,
    sys_path: MutableSequence[str] | None = None,
) -> StartupPaths:
    """Configure import paths for development and PyInstaller runtimes."""
    is_frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if is_frozen:
        application_path = meipass if meipass is not None else getattr(sys, "_MEIPASS")
        bundled_src_path = os.path.join(application_path, src_dir_name)
        if path_exists(bundled_src_path):
            add_sys_path(bundled_src_path, sys_path)
    else:
        application_path = os.path.dirname(os.path.abspath(base_file))
        bundled_src_path = None

    add_sys_path(application_path, sys_path)
    return StartupPaths(application_path, bundled_src_path)
