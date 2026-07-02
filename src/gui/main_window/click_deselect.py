"""Helpers for deciding when a background click should clear task selection."""

from typing import Any, Iterable


def is_widget_or_parent_in(widget: Any, targets: Iterable[Any]) -> bool:
    """Return True when widget or one of its parents is in targets."""
    target_widgets = list(targets)
    current = widget
    while current:
        if current in target_widgets:
            return True
        parent = getattr(current, "parent", None)
        current = parent() if callable(parent) else None
    return False


def should_clear_selection_for_click(
    source: Any,
    click_pos: Any,
    deselect_targets: Iterable[Any],
    task_widgets: Iterable[Any],
) -> bool:
    """Return True when a click on source is outside task widgets."""
    if source not in list(deselect_targets):
        return False

    child_at_pos = source.childAt(click_pos)
    return not is_widget_or_parent_in(child_at_pos, task_widgets)