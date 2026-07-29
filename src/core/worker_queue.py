"""Helpers for parsing DownloadWorker queue entries."""

from typing import Any, Dict, Optional, Tuple

TaskData = Tuple[int, str, Dict, Dict, bool, int]


def parse_task_wrapper(task_wrapper: Any) -> Tuple[Optional[TaskData], bool]:
    """Parse a scheduler-produced task or shutdown marker."""
    if not isinstance(task_wrapper, tuple):
        raise ValueError("Queue entries must be tuples")

    if len(task_wrapper) == 3 and task_wrapper[1:] == (-1, None):
        return None, True

    if len(task_wrapper) != 7:
        raise ValueError(f"Unsupported queue entry shape: {len(task_wrapper)} items")

    _, generation, task_id, url, task_settings, metadata, is_resume = task_wrapper
    return (task_id, url, task_settings, metadata, is_resume, generation), False
