"""Status predicates for task actions."""

from typing import Any

from constants import TaskStatus


PAUSABLE_STATUSES = (TaskStatus.DOWNLOADING, TaskStatus.WAITING)
RESUMABLE_STATUSES = (TaskStatus.PAUSED,)
RETRYABLE_STATUSES = (TaskStatus.FAILED, TaskStatus.FINISHED)


def is_pausable_status(status: Any) -> bool:
    """Return True when a task with this status can be paused."""
    return status in PAUSABLE_STATUSES


def is_resumable_status(status: Any) -> bool:
    """Return True when a task with this status can be resumed."""
    return status in RESUMABLE_STATUSES


def is_retryable_status(status: Any) -> bool:
    """Return True when a task with this status can be retried."""
    return status in RETRYABLE_STATUSES