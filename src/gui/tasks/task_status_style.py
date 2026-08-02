"""Style decisions for task status presentation."""

from typing import Any

from constants import TaskStatus
from resources import colors


def status_border_color(status: Any) -> str:
    """Return the border color used for a task status."""
    status_colors = {
        TaskStatus.DOWNLOADING: colors.COLOR_TASK_DOWNLOADING_BORDER,
        TaskStatus.FINISHED: colors.COLOR_TASK_FINISHED_BORDER,
        TaskStatus.FAILED: colors.COLOR_TASK_FAILED_BORDER,
        TaskStatus.PAUSED: colors.COLOR_TASK_PAUSED_BORDER,
        TaskStatus.WAITING: colors.COLOR_TASK_WAITING_BORDER,
    }
    return status_colors.get(status, colors.COLOR_TASK_WAITING_BORDER)
