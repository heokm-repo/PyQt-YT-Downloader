"""Task-state policy used when the application is about to restart."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from constants import TaskStatus


RESTART_SENSITIVE_STATUSES = frozenset(
    (TaskStatus.DOWNLOADING, TaskStatus.WAITING)
)


def has_restart_sensitive_tasks(tasks: Iterable[Any]) -> bool:
    """Return whether restart will pause a downloading or waiting task."""
    return any(
        getattr(task, "status", None) in RESTART_SENSITIVE_STATUSES
        for task in tasks
    )
