"""Visibility planning for task context menus."""

from dataclasses import dataclass
from typing import Any, Iterable

from constants import TaskStatus


@dataclass(frozen=True)
class ContextMenuStatusFlags:
    finished: bool
    paused: bool
    downloading: bool
    waiting: bool
    failed: bool


@dataclass(frozen=True)
class ContextMenuVisibility:
    play: bool
    open_folder: bool
    copy_url: bool
    pause: bool
    resume: bool
    retry: bool
    delete_file: bool
    remove: bool
    remove_completed: bool


def context_menu_status_flags(tasks: Iterable[Any]) -> ContextMenuStatusFlags:
    """Return status flags for selected tasks."""
    statuses = [getattr(task, "status", None) for task in tasks]
    return ContextMenuStatusFlags(
        finished=TaskStatus.FINISHED in statuses,
        paused=TaskStatus.PAUSED in statuses,
        downloading=TaskStatus.DOWNLOADING in statuses,
        waiting=TaskStatus.WAITING in statuses,
        failed=TaskStatus.FAILED in statuses,
    )


def has_completed_task(tasks: Iterable[Any]) -> bool:
    """Return True when any task is completed."""
    return any(getattr(task, "status", None) == TaskStatus.FINISHED for task in tasks)


def build_context_menu_visibility(
    selected_tasks: Iterable[Any],
    all_tasks: Iterable[Any] | None = None,
) -> ContextMenuVisibility:
    """Return which context-menu actions should be visible."""
    selected_task_list = list(selected_tasks)
    count = len(selected_task_list)
    flags = context_menu_status_flags(selected_task_list)
    single_finished = flags.finished and count == 1

    return ContextMenuVisibility(
        play=single_finished,
        open_folder=single_finished,
        copy_url=count == 1,
        pause=flags.downloading or flags.waiting,
        resume=flags.paused,
        retry=flags.failed or flags.finished,
        delete_file=flags.finished,
        remove=True,
        remove_completed=has_completed_task(all_tasks or []),
    )
