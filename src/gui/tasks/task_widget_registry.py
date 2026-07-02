"""TaskWidget registration helpers for the main window."""

from typing import Any, Callable, MutableMapping, Optional


def apply_task_title_override(task_widget: Any, settings: dict, title_override: Optional[str]) -> None:
    """Apply a playlist-style title override to a task widget when provided."""
    if not title_override:
        return

    task_format = settings.get("format", "mp4").upper()
    task_widget.title_label.setText(f"[{task_format}] {title_override}")


def register_task_widget(
    task_widget: Any,
    task_id: int,
    task_layout: Any,
    task_widgets: MutableMapping[int, Any],
    connect_signals: Callable[[Any], None],
) -> None:
    """Wire a task widget and insert it at the top of the task list."""
    connect_signals(task_widget)
    task_layout.insertWidget(0, task_widget)
    task_widgets[task_id] = task_widget


def create_registered_task_widget(
    task_id: int,
    url: str,
    settings: dict,
    title_override: Optional[str],
    parent: Any,
    task_layout: Any,
    task_widgets: MutableMapping[int, Any],
    connect_signals: Callable[[Any], None],
    widget_factory: Optional[Callable[[int, str, dict, Any], Any]] = None,
) -> Any:
    """Create a TaskWidget, apply display overrides, and register it."""
    if widget_factory is None:
        from gui.widgets.task_item import TaskWidget

        widget_factory = TaskWidget

    task_widget = widget_factory(task_id, url, settings, parent)
    apply_task_title_override(task_widget, settings, title_override)
    register_task_widget(
        task_widget,
        task_id,
        task_layout,
        task_widgets,
        connect_signals,
    )
    return task_widget