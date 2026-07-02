"""Cleanup behavior for paused tasks that the user chooses not to resume."""

import os
import shutil
from typing import Any, Mapping, Sequence

from constants import TaskStatus, YTDL_TEMP_DIR
from locales.strings import STR
from utils.logger import log
from utils.settings_store import get_download_folder


def cleanup_cancelled_paused_tasks(tasks: Sequence[Any], task_widgets: Mapping[int, Any]) -> None:
    """Delete temp folders once per save path and mark paused tasks as failed."""
    cleaned_dirs = set()
    for task in tasks:
        save_path = get_download_folder(task.settings)
        if save_path and save_path not in cleaned_dirs:
            temp_dir = os.path.join(save_path, YTDL_TEMP_DIR)
            if os.path.isdir(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    log.info(f"임시 폴더 삭제: {temp_dir}")
                except Exception as exc:
                    log.warning(f"임시 폴더 삭제 실패: {temp_dir}: {exc}")
            cleaned_dirs.add(save_path)

        task.status = TaskStatus.FAILED
        widget = task_widgets.get(task.id)
        if widget:
            widget.set_failed(STR.STATUS_PAUSED_CANCELLED)
