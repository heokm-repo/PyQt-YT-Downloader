"""Cleanup behavior for paused tasks that the user chooses not to resume."""

from typing import Any, Mapping, Sequence

from constants import TaskStatus
from core.download.workspace_cleanup import remove_workspace_cleanup_request
from gui.tasks.task_workspace_cleanup import build_task_cleanup_request
from locales.strings import STR
from utils.logger import log


def cleanup_cancelled_paused_tasks(
    tasks: Sequence[Any],
    task_widgets: Mapping[int, Any],
) -> None:
    """Delete only each declined task workspace and mark it as failed."""
    for task in tasks:
        cleanup_request = build_task_cleanup_request(task)
        removed = remove_workspace_cleanup_request(cleanup_request)
        if not removed:
            log.warning(
                "Failed to discard paused task workspace: %s",
                getattr(task, "id", "unknown"),
            )

        task.status = TaskStatus.FAILED
        widget = task_widgets.get(task.id)
        if widget:
            widget.set_failed(STR.STATUS_PAUSED_CANCELLED)
