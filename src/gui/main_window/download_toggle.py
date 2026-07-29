"""Helpers for applying the global download toggle."""

from dataclasses import dataclass
from typing import Any, Mapping, MutableSequence

from constants import TaskStatus
from gui.tasks.task_resume_plan import build_resume_task_plan


@dataclass(frozen=True)
class DownloadTogglePlan:
    enabled: bool
    status_text: str


def build_download_toggle_plan(
    current_enabled: bool,
    enabled_text: str,
    paused_text: str,
) -> DownloadTogglePlan:
    """Return the next global-download toggle state and status text."""
    enabled = not current_enabled
    return DownloadTogglePlan(
        enabled=enabled,
        status_text=enabled_text if enabled else paused_text,
    )


def resume_paused_tasks(
    tasks: MutableSequence[Any],
    task_widgets: Mapping[int, Any],
    scheduler: Any,
    default_settings: Mapping[str, Any],
    waiting_text: str,
) -> None:
    """Requeue paused tasks when the global download toggle is enabled."""
    for task in tasks:
        if task.status != TaskStatus.PAUSED:
            continue

        resume_plan = build_resume_task_plan(task, default_settings)
        if resume_plan is None:
            continue

        if scheduler.is_task_paused(task.id):
            scheduler.resume_task(task.id)

        widget = task_widgets.get(task.id)
        if widget:
            widget.set_status("waiting")
            widget.status_label.setText(waiting_text)

        task.status = TaskStatus.WAITING

        scheduler.add_task(
            1,
            task.id,
            resume_plan.url,
            resume_plan.settings,
            resume_plan.meta,
            is_resume=True,
        )


def mark_downloading_tasks_paused(tasks: MutableSequence[Any]) -> list[int]:
    """Mark currently downloading tasks as paused and return changed task ids."""
    paused_ids = []
    for task in tasks:
        if task.status != TaskStatus.DOWNLOADING:
            continue

        task.status = TaskStatus.PAUSED
        paused_ids.append(task.id)
    return paused_ids


def pause_downloading_tasks(tasks: MutableSequence[Any], task_widgets: Mapping[int, Any]) -> None:
    """Mark currently downloading tasks as paused before pausing workers."""
    for task_id in mark_downloading_tasks_paused(tasks):
        widget = task_widgets.get(task_id)
        if widget:
            widget.set_paused()
