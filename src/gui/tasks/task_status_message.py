"""Build user-facing status text for the task list."""

from typing import Any, Sequence

from core.task_summary import summarize_task_progress


def build_task_status_message(
    tasks: Sequence[Any],
    ready_message: str,
    error_template: str,
    completed_template: str,
) -> str:
    """Return the status bar text for the current task collection."""
    if not tasks:
        return ready_message

    summary = summarize_task_progress(tasks)
    if summary.has_failures:
        return error_template.format(count=summary.failed)

    return completed_template.format(finished=summary.finished, total=summary.total)