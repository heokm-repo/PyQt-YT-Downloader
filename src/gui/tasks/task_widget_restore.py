"""Restore TaskWidget state from persisted task data."""

from typing import Any, Callable, MutableMapping, Optional

from constants import TaskStatus
from gui.tasks.task_widget_registry import register_task_widget
from locales.strings import STR


def restore_task_widget_state(widget: Any, task: Any) -> None:
    """Apply saved metadata and status to a task widget."""
    if task.meta:
        widget.update_metadata(task.meta)

    if task.status == TaskStatus.FINISHED:
        widget.set_finished(file_size=task.meta.get("file_size"))
    elif task.status == TaskStatus.PAUSED:
        widget.set_paused()
        widget.status_label.setText(STR.STATUS_PAUSED_SAVED)
        widget.percent_label.setText(STR.STATUS_WAITING_DOTS)
    elif task.status == TaskStatus.FAILED:
        widget.set_failed(STR.STATUS_IN_PROGRESS)


def create_restored_task_widget(
    task: Any,
    parent: Any,
    task_layout: Any,
    task_widgets: MutableMapping[int, Any],
    connect_signals: Callable[[Any], None],
    widget_factory: Optional[Callable[[int, str, dict, Any], Any]] = None,
) -> Any:
    """Create, register, and restore a TaskWidget for a loaded task."""
    if widget_factory is None:
        from gui.widgets.task_item import TaskWidget

        widget_factory = TaskWidget

    task_widget = widget_factory(task.id, task.url, task.settings, parent)
    register_task_widget(
        task_widget,
        task.id,
        task_layout,
        task_widgets,
        connect_signals,
    )
    restore_task_widget_state(task_widget, task)
    return task_widget