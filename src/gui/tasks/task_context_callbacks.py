"""Build callback maps for task context menus."""

from typing import Any, Callable, Dict, Sequence


def build_task_context_callbacks(window: Any, selected_ids: Sequence[int]) -> Dict[str, Callable[[], Any]]:
    """Create context-menu callbacks for the current task selection."""
    first_id = selected_ids[0] if selected_ids else None

    return {
        "play": lambda: window.play_file(first_id) if first_id is not None else None,
        "open_folder": window._open_folders_for_selected,
        "copy_url": lambda: window.task_actions.copy_url(first_id) if first_id is not None else None,
        "pause": window._pause_selected_tasks,
        "resume": window._resume_selected_tasks,
        "retry": window._retry_selected_tasks,
        "delete_file": window._delete_files_for_selected,
        "remove": window._remove_selected_from_list,
        "remove_all_completed": window._remove_all_completed_from_list,
    }
