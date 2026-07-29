"""Build task objects and restore decisions from persisted task data."""

from dataclasses import dataclass
from typing import Callable, Iterable, List, Sequence, Tuple

from constants import TaskStatus
from core.download.workspace_identity import is_workspace_id
from data.models import DownloadTask


@dataclass(frozen=True)
class PausedTaskRestoreResult:
    """Result of handling paused tasks after loading persisted tasks."""

    paused_count: int
    resumed: bool
    cleaned_up: bool


def build_loaded_tasks(task_data_items: Iterable[dict]) -> Tuple[List[DownloadTask], int]:
    """Convert persisted task dictionaries to task objects and return max task id."""
    tasks = [DownloadTask.from_dict(task_data) for task_data in task_data_items]
    max_id = max((task.id for task in tasks), default=0)
    return tasks, max_id


def loaded_tasks_need_workspace_persistence(
    task_data_items: Iterable[dict],
) -> bool:
    """Return whether legacy task data needs its assigned UUID saved now."""
    return any(
        not is_workspace_id(task_data.get("workspace_id"))
        for task_data in task_data_items
    )


def find_paused_tasks(tasks: Iterable[DownloadTask]) -> List[DownloadTask]:
    """Return persisted tasks that should prompt for resume."""
    return [task for task in tasks if task.status == TaskStatus.PAUSED]


def handle_paused_task_restore(
    tasks: Iterable[DownloadTask],
    confirm_resume: Callable[[], bool],
    resume_task: Callable[[int], None],
    cleanup_tasks: Callable[[Sequence[DownloadTask]], None],
) -> PausedTaskRestoreResult:
    """Resume or clean up paused tasks after asking for user confirmation."""
    paused_tasks = find_paused_tasks(tasks)
    if not paused_tasks:
        return PausedTaskRestoreResult(paused_count=0, resumed=False, cleaned_up=False)

    if confirm_resume():
        for task in paused_tasks:
            resume_task(task.id)
        return PausedTaskRestoreResult(
            paused_count=len(paused_tasks), resumed=True, cleaned_up=False
        )

    cleanup_tasks(paused_tasks)
    return PausedTaskRestoreResult(
        paused_count=len(paused_tasks), resumed=False, cleaned_up=True
    )
