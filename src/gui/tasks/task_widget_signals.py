"""Signal wiring helpers for TaskWidget instances."""

from typing import Any


def connect_task_widget_signals(task_widget: Any, window: Any) -> None:
    """Connect a TaskWidget's signals to the main window handlers."""
    task_widget.remove_requested.connect(window.remove_task_from_list)
    task_widget.pause_requested.connect(window.pause_task)
    task_widget.resume_requested.connect(window.resume_task)
    task_widget.retry_requested.connect(window.retry_task)
    task_widget.play_requested.connect(window.play_file)
    task_widget.open_folder_requested.connect(window.open_folder)
    task_widget.delete_file_requested.connect(lambda task_id: window.delete_file(task_id, True))
    task_widget.clicked.connect(window.on_task_clicked)
    task_widget.right_clicked.connect(window.show_context_menu)
