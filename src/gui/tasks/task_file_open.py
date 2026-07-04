"""File opening helpers for task actions."""

import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

from constants import WINDOWS_EXPLORER_COMMAND, WINDOWS_EXPLORER_SELECT_PREFIX
from gui.tasks.task_file_paths import existing_file_path, normalize_output_path, resolve_open_folder_target


class OpenFileStatus(Enum):
    NO_PATH = "no_path"
    MISSING = "missing"
    OPENED = "opened"
    ERROR = "error"


class OpenFolderStatus(Enum):
    NO_TARGET = "no_target"
    OPENED = "opened"
    ERROR = "error"


@dataclass(frozen=True)
class OpenFileResult:
    status: OpenFileStatus
    output_path: str = ""
    file_path: str = ""
    error: Optional[BaseException] = None


@dataclass(frozen=True)
class OpenFolderResult:
    status: OpenFolderStatus
    path: str = ""
    select_file: bool = False
    error: Optional[BaseException] = None


def open_output_file(
    output_path: str,
    start_file: Optional[Callable[[str], None]] = None,
) -> OpenFileResult:
    """Open a task output file and return the outcome without showing UI."""
    normalized_path = normalize_output_path(output_path)
    if not normalized_path:
        return OpenFileResult(OpenFileStatus.NO_PATH)

    file_path = existing_file_path(normalized_path)
    if not file_path:
        return OpenFileResult(
            OpenFileStatus.MISSING,
            output_path=normalized_path,
        )

    start_file = start_file or os.startfile
    try:
        start_file(file_path)
    except Exception as error:
        return OpenFileResult(
            OpenFileStatus.ERROR,
            output_path=normalized_path,
            file_path=file_path,
            error=error,
        )

    return OpenFileResult(
        OpenFileStatus.OPENED,
        output_path=normalized_path,
        file_path=file_path,
    )


def _open_selected_file_in_explorer(path: str) -> None:
    subprocess.Popen([WINDOWS_EXPLORER_COMMAND, f"{WINDOWS_EXPLORER_SELECT_PREFIX}{path}"])


def open_output_folder(
    output_path: str,
    start_file: Optional[Callable[[str], None]] = None,
    select_file: Callable[[str], None] = _open_selected_file_in_explorer,
) -> OpenFolderResult:
    """Open the best folder target for a task output path."""
    target = resolve_open_folder_target(output_path)
    if not target:
        return OpenFolderResult(OpenFolderStatus.NO_TARGET)

    start_file = start_file or os.startfile
    try:
        if target.select_file:
            select_file(target.path)
        else:
            start_file(target.path)
    except Exception as error:
        return OpenFolderResult(
            OpenFolderStatus.ERROR,
            path=target.path,
            select_file=target.select_file,
            error=error,
        )

    return OpenFolderResult(
        OpenFolderStatus.OPENED,
        path=target.path,
        select_file=target.select_file,
    )
