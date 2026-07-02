"""Helpers for deciding what was clicked inside a task widget."""

from typing import Any


def _parent_of(widget: Any) -> Any:
    parent = getattr(widget, "parent", None)
    if callable(parent):
        return parent()
    return None


def is_click_on_child_type(clicked_widget: Any, root_widget: Any, target_type: Any) -> bool:
    """Return True when clicked_widget or one of its parents is target_type before root."""
    widget = clicked_widget
    while widget is not None and widget is not root_widget:
        if isinstance(widget, target_type):
            return True
        widget = _parent_of(widget)
    return False
