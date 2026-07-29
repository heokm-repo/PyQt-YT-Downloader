"""Planning helpers for bulk task actions."""

from dataclasses import dataclass
from typing import Any, Iterable, Sequence

from constants import TaskStatus
from gui.tasks.task_file_paths import existing_parent_folder
from gui.tasks.task_selection_plan import (
    should_confirm_multiple_items,
    task_ids_with_status,
)


@dataclass(frozen=True)
class BulkTaskActionPlan:
    task_ids: list[int]
    needs_confirmation: bool

    @property
    def count(self) -> int:
        return len(self.task_ids)

    @property
    def has_tasks(self) -> bool:
        return bool(self.task_ids)


def build_delete_files_plan(
    selected_ids: Sequence[int], tasks: Iterable[Any]
) -> BulkTaskActionPlan:
    """Return selected tasks that have a completed or retained media file."""
    tasks_by_id = {task.id: task for task in tasks}
    task_ids = []
    for task_id in selected_ids:
        task = tasks_by_id.get(task_id)
        if not task:
            continue
        if (
            getattr(task, "status", None) == TaskStatus.FINISHED
            or (
                getattr(task, "status", None)
                in (TaskStatus.FAILED, TaskStatus.PAUSED)
                and bool(getattr(task, "output_path", ""))
            )
        ):
            task_ids.append(task_id)
    return BulkTaskActionPlan(task_ids, needs_confirmation=bool(task_ids))


def build_remove_selected_plan(selected_ids: Sequence[int]) -> BulkTaskActionPlan:
    """Return selected task IDs and whether removing them needs confirmation."""
    task_ids = list(selected_ids)
    return BulkTaskActionPlan(
        task_ids,
        needs_confirmation=should_confirm_multiple_items(len(task_ids)),
    )


def build_remove_completed_plan(tasks: Iterable[Any]) -> BulkTaskActionPlan:
    """Return completed task IDs and whether removing them needs confirmation."""
    task_ids = task_ids_with_status(tasks, TaskStatus.FINISHED)
    return BulkTaskActionPlan(
        task_ids,
        needs_confirmation=should_confirm_multiple_items(len(task_ids)),
    )


def folders_to_open_for_selected(
    selected_ids: Sequence[int], tasks: Iterable[Any]
) -> list[str]:
    """Return unique existing parent folders for selected tasks in selection order."""
    tasks_by_id = {task.id: task for task in tasks}
    seen_folders: set[str] = set()
    folders: list[str] = []

    for task_id in selected_ids:
        task = tasks_by_id.get(task_id)
        output_path = getattr(task, "output_path", "") if task else ""
        folder = existing_parent_folder(output_path)
        if folder and folder not in seen_folders:
            seen_folders.add(folder)
            folders.append(folder)

    return folders
