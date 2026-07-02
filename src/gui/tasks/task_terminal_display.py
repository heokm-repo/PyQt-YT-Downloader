"""Display values for terminal task states in task widgets."""

from dataclasses import dataclass
from typing import Any

from constants import MSG_0_PERCENT, TaskStatus
from locales.strings import STR
from resources.styles import (
    PROGRESS_BAR_ERROR_STYLE,
    PROGRESS_BAR_FINISHED_STYLE,
    STATUS_LABEL_ERROR_STYLE,
    STATUS_LABEL_SUCCESS_STYLE,
    STATUS_LABEL_WARNING_STYLE,
)
from utils.utils import format_bytes


@dataclass(frozen=True)
class TaskTerminalDisplay:
    status: TaskStatus
    status_text: str
    status_style: str | None = None
    progress_style: str | None = None
    progress_value: int | None = None
    percent_text: str | None = None
    size_text: str | None = None


def build_finished_display(file_size: Any = None) -> TaskTerminalDisplay:
    """Return display values for a completed task."""
    size_text = format_bytes(file_size) if file_size is not None else None
    return TaskTerminalDisplay(
        status=TaskStatus.FINISHED,
        status_text=STR.STATUS_COMPLETED,
        status_style=STATUS_LABEL_SUCCESS_STYLE,
        progress_style=PROGRESS_BAR_FINISHED_STYLE,
        progress_value=100,
        percent_text=MSG_0_PERCENT.replace("0", "100"),
        size_text=size_text,
    )


def build_failed_display(message: str) -> TaskTerminalDisplay:
    """Return display values for a failed task."""
    return TaskTerminalDisplay(
        status=TaskStatus.FAILED,
        status_text=STR.STATUS_FAILED_FMT.format(message=message),
        status_style=STATUS_LABEL_ERROR_STYLE,
        progress_style=PROGRESS_BAR_ERROR_STYLE,
    )


def build_paused_display() -> TaskTerminalDisplay:
    """Return display values for a paused task."""
    return TaskTerminalDisplay(
        status=TaskStatus.PAUSED,
        status_text=STR.STATUS_PAUSED,
        status_style=STATUS_LABEL_WARNING_STYLE,
    )


def build_started_display() -> TaskTerminalDisplay:
    """Return display values for a task that has just started."""
    return TaskTerminalDisplay(
        status=TaskStatus.DOWNLOADING,
        status_text=STR.STATUS_PREPARING,
    )