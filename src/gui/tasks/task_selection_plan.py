"""Helpers for deciding which task IDs bulk actions should affect."""

from typing import Any, Callable, Iterable, Sequence


def selected_tasks_for_ids(selected_ids: Sequence[int], tasks: Iterable[Any]) -> list[Any]:
    """Return task objects matching selected IDs in task-list order."""
    selected_id_set = set(selected_ids)
    return [task for task in tasks if task.id in selected_id_set]


def tasks_except_id(tasks: Iterable[Any], task_id: int) -> list[Any]:
    """Return tasks excluding the task with the given ID."""
    return [task for task in tasks if task.id != task_id]


def selected_task_ids_matching(
    selected_ids: Sequence[int],
    tasks: Iterable[Any],
    predicate: Callable[[Any], bool],
) -> list[int]:
    """Return selected task IDs whose task matches the predicate."""
    tasks_by_id = {task.id: task for task in tasks}
    matching_ids: list[int] = []
    for task_id in selected_ids:
        task = tasks_by_id.get(task_id)
        if task and predicate(task):
            matching_ids.append(task_id)
    return matching_ids




def task_ids_with_status(tasks: Iterable[Any], status: Any) -> list[int]:
    """Return task IDs whose task has the requested status."""
    return [task.id for task in tasks if task.status == status]


def should_confirm_multiple_items(count: int) -> bool:
    """Return True when a bulk action should ask for multi-item confirmation."""
    return count > 1
