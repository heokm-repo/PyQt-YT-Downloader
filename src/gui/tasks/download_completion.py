"""Helpers for applying completed download results to UI state."""

import os
from enum import Enum
from typing import Any

from constants import TaskStatus
from utils.logger import log


class FailedDownloadAction(Enum):
    IGNORE_ALREADY_PAUSED = "ignore_already_paused"
    IGNORE_RESUMING = "ignore_resuming"
    PAUSE = "pause"
    FAIL = "fail"


def persist_download_output(task: Any, final_path: str, success: bool) -> str:
    """Store output path and file size on a task when available."""
    if not task or not final_path:
        return final_path

    resolved_path = final_path
    if not os.path.isabs(resolved_path):
        resolved_path = os.path.abspath(resolved_path)
    task.output_path = resolved_path

    if success and os.path.exists(resolved_path):
        try:
            task.meta["file_size"] = os.path.getsize(resolved_path)
        except Exception as exc:
            log.warning(f"Failed to store file size: {exc}")

    return resolved_path


def resolve_failed_download_action(task: Any, message: str, paused_message: str) -> FailedDownloadAction:
    """Decide how a failed download result should affect task/widget state."""
    if message != paused_message:
        return FailedDownloadAction.FAIL

    if task and task.status == TaskStatus.PAUSED:
        return FailedDownloadAction.IGNORE_ALREADY_PAUSED

    if task and task.status == TaskStatus.WAITING:
        return FailedDownloadAction.IGNORE_RESUMING

    return FailedDownloadAction.PAUSE


def record_successful_download(
    task: Any,
    history_manager: Any,
    default_format: str = "mp4",
) -> Any:
    """Mark a task finished, persist it to history, and return its file size."""
    if not task:
        return None

    task.status = TaskStatus.FINISHED
    task_format = task.settings.get("format", default_format)
    history_manager.add_to_history(task.extractor, task.video_id, task.meta, task_format)
    return task.meta.get("file_size")


def apply_failed_download_result(
    task: Any,
    widget: Any,
    message: str,
    paused_message: str,
) -> FailedDownloadAction:
    """Apply a failed download result to task and widget state."""
    action = resolve_failed_download_action(task, message, paused_message)

    if action in (
        FailedDownloadAction.IGNORE_ALREADY_PAUSED,
        FailedDownloadAction.IGNORE_RESUMING,
    ):
        return action

    if action == FailedDownloadAction.PAUSE:
        if task:
            task.status = TaskStatus.PAUSED
        widget.set_paused()
        return action

    if task:
        task.status = TaskStatus.FAILED
    widget.set_failed(message)
    return action
