"""Build and execute task registration for the main window."""

from dataclasses import dataclass
from typing import Any, Callable, Mapping, MutableMapping, MutableSequence, Optional

from data.models import DownloadTask
from gui.tasks.task_widget_registry import create_registered_task_widget
from gui.tasks.task_workspace_payload import build_workspace_execution_settings


NORMAL_TASK_PRIORITY = 3


@dataclass(frozen=True)
class TaskRegistrationPlan:
    task: DownloadTask
    settings: dict
    title_override: Optional[str]
    scheduler_priority: int = NORMAL_TASK_PRIORITY


def build_task_registration_plan(
    task_id: int,
    url: str,
    settings: Mapping[str, Any],
    video_id: Optional[str] = None,
    extractor: str = "unknown",
    title_override: Optional[str] = None,
) -> TaskRegistrationPlan:
    """Return copied settings and a task object ready for registration."""
    current_settings = dict(settings)
    task = DownloadTask(
        id=task_id,
        url=url,
        video_id=video_id,
        extractor=extractor,
        settings=current_settings,
    )
    return TaskRegistrationPlan(
        task=task,
        settings=current_settings,
        title_override=title_override,
    )


def register_download_task(
    task_id: int,
    url: str,
    settings: Mapping[str, Any],
    parent: Any,
    task_layout: Any,
    task_widgets: MutableMapping[int, Any],
    connect_signals: Callable[[Any], None],
    tasks: MutableSequence[DownloadTask],
    scheduler: Any,
    video_id: Optional[str] = None,
    extractor: str = "unknown",
    title_override: Optional[str] = None,
    widget_factory: Optional[Callable[[int, str, dict, Any], Any]] = None,
) -> DownloadTask:
    """Create the task, register its widget, store it, and enqueue it."""
    registration = build_task_registration_plan(
        task_id,
        url,
        settings,
        video_id,
        extractor,
        title_override,
    )

    create_registered_task_widget(
        task_id,
        url,
        registration.settings,
        registration.title_override,
        parent,
        task_layout,
        task_widgets,
        connect_signals,
        widget_factory,
    )

    tasks.append(registration.task)
    execution_settings = build_workspace_execution_settings(
        registration.task,
        registration.settings,
        resume=False,
    )
    scheduler.add_task(
        registration.scheduler_priority,
        task_id,
        url,
        execution_settings,
        {
            "id": registration.task.video_id,
            "extractor": registration.task.extractor,
        },
    )
    return registration.task
