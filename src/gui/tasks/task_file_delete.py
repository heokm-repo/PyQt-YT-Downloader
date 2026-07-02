"""File deletion helpers for task actions."""

import os
from dataclasses import dataclass
from enum import Enum
from types import TracebackType
from typing import Callable, Optional, Tuple, Type

from gui.tasks.task_file_paths import existing_file_path, normalize_output_path


class DeleteFileStatus(Enum):
    NO_PATH = "no_path"
    MISSING = "missing"
    NOT_FILE = "not_file"
    DELETED = "deleted"
    PERMISSION_ERROR = "permission_error"
    ERROR = "error"


@dataclass(frozen=True)
class DeleteFileResult:
    status: DeleteFileStatus
    output_path: str = ""
    file_path: str = ""
    error: Optional[BaseException] = None

    @property
    def exc_info(
        self,
    ) -> Optional[Tuple[Type[BaseException], BaseException, Optional[TracebackType]]]:
        if not self.error:
            return None
        return (type(self.error), self.error, self.error.__traceback__)


def delete_output_file(
    output_path: str,
    remove_file: Callable[[str], None] = os.remove,
) -> DeleteFileResult:
    """Delete a task output file and return the outcome without showing UI."""
    normalized_path = normalize_output_path(output_path)
    if not normalized_path:
        return DeleteFileResult(DeleteFileStatus.NO_PATH)

    file_path = existing_file_path(normalized_path)
    if not file_path:
        if os.path.exists(normalized_path):
            return DeleteFileResult(
                DeleteFileStatus.NOT_FILE,
                output_path=normalized_path,
            )
        return DeleteFileResult(
            DeleteFileStatus.MISSING,
            output_path=normalized_path,
        )

    try:
        remove_file(file_path)
    except PermissionError as error:
        return DeleteFileResult(
            DeleteFileStatus.PERMISSION_ERROR,
            output_path=normalized_path,
            file_path=file_path,
            error=error,
        )
    except Exception as error:
        return DeleteFileResult(
            DeleteFileStatus.ERROR,
            output_path=normalized_path,
            file_path=file_path,
            error=error,
        )

    return DeleteFileResult(
        DeleteFileStatus.DELETED,
        output_path=normalized_path,
        file_path=file_path,
    )
