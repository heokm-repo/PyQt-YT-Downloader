"""Remove yt-dlp temporary directories after every task succeeds."""

import os
import shutil
from typing import Any, Sequence

from constants import TaskStatus, YTDL_TEMP_DIR
from utils.logger import log
from utils.settings_store import get_download_folder


def cleanup_temp_dirs_if_all_finished(tasks: Sequence[Any]) -> list[str]:
    """Remove temp directories only when every task has finished successfully."""
    if not tasks or any(task.status != TaskStatus.FINISHED for task in tasks):
        return []

    removed_dirs = []
    checked_paths = set()

    for task in tasks:
        save_path = get_download_folder(task.settings)
        if not save_path or save_path in checked_paths:
            continue

        checked_paths.add(save_path)
        temp_dir = os.path.join(save_path, YTDL_TEMP_DIR)
        if not os.path.isdir(temp_dir):
            continue

        try:
            shutil.rmtree(temp_dir)
            removed_dirs.append(temp_dir)
            log.info(f"Removed completed download temp directory: {temp_dir}")
        except OSError as exc:
            log.warning(f"Failed to remove completed download temp directory: {temp_dir}: {exc}")

    return removed_dirs
