"""Helpers for parsing DownloadWorker queue entries."""

from typing import Any, Dict, Optional, Tuple

TaskData = Tuple[int, str, Dict, Dict, bool, Optional[int]]


def parse_task_wrapper(task_wrapper: Any) -> Tuple[Optional[TaskData], bool]:
    """Return parsed task data and whether the queue item is already complete."""
    if task_wrapper is None:
        return None, False

    generation = None
    if isinstance(task_wrapper, tuple):
        if len(task_wrapper) == 2 and task_wrapper[1] is None:
            return None, True
        if len(task_wrapper) >= 3 and task_wrapper[2] is None:
            return None, True

        if len(task_wrapper) == 7:
            _, generation, task_id, url, task_settings, metadata, is_resume = task_wrapper
        elif len(task_wrapper) == 6:
            _, task_id, url, task_settings, metadata, is_resume = task_wrapper
        elif len(task_wrapper) == 5:
            _, task_id, url, task_settings, metadata = task_wrapper
            is_resume = False
        else:
            task_id, url, task_settings = task_wrapper[1:4]
            metadata = {}
            is_resume = False
    else:
        task = task_wrapper
        if len(task) == 5:
            task_id, url, task_settings, metadata, is_resume = task
        elif len(task) == 4:
            task_id, url, task_settings, metadata = task
            is_resume = False
        else:
            task_id, url, task_settings = task
            metadata = {}
            is_resume = False

    return (task_id, url, task_settings, metadata, is_resume, generation), False
