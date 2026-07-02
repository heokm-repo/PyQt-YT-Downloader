"""Style decisions for task status presentation."""

from typing import Any

from constants import TaskStatus
from resources.styles import (
    COLOR_DOWNLOADING,
    COLOR_ERROR,
    COLOR_FINISHED,
    COLOR_PAUSED,
    COLOR_WAITING,
)


STATUS_BORDER_COLORS = {
    TaskStatus.DOWNLOADING: COLOR_DOWNLOADING,
    TaskStatus.FINISHED: COLOR_FINISHED,
    TaskStatus.FAILED: COLOR_ERROR,
    TaskStatus.PAUSED: COLOR_PAUSED,
    TaskStatus.WAITING: COLOR_WAITING,
}


def status_border_color(status: Any) -> str:
    """Return the border color used for a task status."""
    return STATUS_BORDER_COLORS.get(status, COLOR_WAITING)