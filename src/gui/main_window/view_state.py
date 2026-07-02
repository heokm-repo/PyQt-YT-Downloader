"""Small view-state helpers for the main window."""

from typing import Mapping


def show_task_list(scroll_area, empty_label) -> bool:
    """Show the task list when it is currently hidden."""
    if not scroll_area.isHidden():
        return False

    empty_label.hide()
    scroll_area.show()
    return True


def hide_task_list_if_empty(task_widgets: Mapping[int, object], scroll_area, empty_label) -> bool:
    """Show the empty state when no task widgets remain."""
    if task_widgets:
        return False

    empty_label.show()
    scroll_area.hide()
    return True


def set_url_entry_enabled(url_input, download_button, enabled: bool) -> None:
    """Enable or disable the URL input and its primary action button together."""
    url_input.setEnabled(enabled)
    download_button.setEnabled(enabled)