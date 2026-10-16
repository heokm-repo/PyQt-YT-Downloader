"""Helpers for applying completed download results to UI state."""

import os
from enum import Enum
from typing import Any

from constants import TaskStatus
from utils.logger import log
from locales.strings import STR


class FailedDownloadAction(Enum):
    IGNORE_ALREADY_PAUSED = "ignore_already_paused"
    IGNORE_RESUMING = "ignore_resuming"
    PAUSE = "pause"
    FAIL = "fail"


def completed_media_items(task):
    return [item for item in (getattr(task, 'meta', {}) or {}).get('media_items', [])
            if isinstance(item, dict) and item.get('state') == 'completed' and item.get('output_path')]


def task_output_paths(task):
    items = completed_media_items(task)
    if items:
        return list(dict.fromkeys(item['output_path'] for item in items))
    return [task.output_path] if getattr(task, 'output_path', '') else []


def media_completion_summary(task):
    items = (getattr(task, 'meta', {}) or {}).get('media_items')
    if items is None:
        return ''
    total = sum(item.get('kind') != 'image' for item in items)
    return (STR.STATUS_COMPLETED_COUNT.format(done=len(completed_media_items(task)), total=total)
            if total > 1 else STR.STATUS_COMPLETED)


def media_failure_summary(task, message):
    items = (getattr(task, 'meta', {}) or {}).get('media_items') or []
    total = sum(item.get('kind') != 'image' for item in items)
    return (STR.STATUS_FAILED_COUNT_FMT.format(done=len(completed_media_items(task)), total=total, message=message)
            if total > 1 else STR.STATUS_FAILED_FMT.format(message=message))


def record_completed_media(task, history_manager, default_format='mp4'):
    for item in completed_media_items(task):
        history_manager.add_to_history(item['extractor'], item['id'], item,
                                       task.settings.get('format', default_format))


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
            task.meta["file_size"] = sum(os.path.getsize(path) for path in task_output_paths(task)
                                         if os.path.isfile(path))
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
    task.meta.pop('download_error', None)
    task_format = task.settings.get("format", default_format)
    if task.meta.get('media_items'):
        record_completed_media(task, history_manager, default_format)
    else:
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
        task.meta['download_error'] = message
    widget.set_failed(message)
    if task and task.meta.get('media_items'):
        widget.status_label.setText(media_failure_summary(task, message))
    return action
