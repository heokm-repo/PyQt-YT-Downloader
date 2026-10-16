"""Duplicate facts only; confirmation text and dialogs belong to the GUI."""
from dataclasses import dataclass

from constants import DEFAULT_FORMAT, TaskStatus
from data.models import DownloadTask


@dataclass(frozen=True)
class DuplicateResult:
    in_history: bool
    target_format: str = DEFAULT_FORMAT
    duplicate_task: DownloadTask | None = None
    queue_status: TaskStatus | None = None

    @property
    def is_duplicate(self) -> bool:
        return self.in_history or self.duplicate_task is not None


def active_duplicate_keys(tasks):
    """Take a request-local snapshot of active extractor/ID/format keys."""
    keys = set()
    for task in tasks:
        if not task.is_active():
            continue
        key = (getattr(task, 'extractor', None), getattr(task, 'video_id', None),
               (getattr(task, 'settings', {}) or {}).get('format', DEFAULT_FORMAT))
        # Malformed persisted metadata cannot match a string playlist target.
        if all(isinstance(value, str) for value in key):
            keys.add(key)
    return keys


class DuplicateChecker:
    def __init__(self, history_manager):
        self.history_manager = history_manager

    def check(self, extractor, video_id, current_task_id, tasks, target_ext=DEFAULT_FORMAT):
        in_history = self.history_manager.is_downloaded(extractor, video_id, target_ext)
        duplicate = next((task for task in tasks
                          if task.id != current_task_id and task.extractor == extractor
                          and task.video_id == video_id
                          and task.settings.get('format', DEFAULT_FORMAT) == target_ext
                          and task.is_active()), None)
        return DuplicateResult(in_history, target_ext, duplicate,
                               duplicate.status if duplicate is not None else None)
