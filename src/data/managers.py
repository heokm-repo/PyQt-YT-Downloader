"""Task persistence and compatibility exports for the separated data services."""
import os
from collections.abc import Iterable

from constants import TaskStatus, TASKS_JSON_FILENAME
from data.duplicate_checker import DuplicateChecker
from data.history_store import HistoryManager
from data.models import DownloadTask
from data.task_validation import valid_task_records
from utils.app_paths import get_user_data_path
from utils.json_store import read_json, write_json_atomic
from utils.logger import log


class TaskManager:
    """Manage the saved task list."""
    
    def __init__(self):
        self.tasks_file = os.path.join(get_user_data_path(), TASKS_JSON_FILENAME)
    
    def save_tasks(self, tasks: Iterable[DownloadTask]):
        """Save the current task list to a JSON file."""
        serializable_tasks = []
        for task in tasks:
            # Normalize active or waiting tasks to Paused before saving,
            # so they do not auto-start on the next launch.
            status = task.status
            if status in [TaskStatus.DOWNLOADING, TaskStatus.WAITING]:
                status = TaskStatus.PAUSED
            
            # Convert DownloadTask to a dictionary.
            task_dict = task.to_dict()
            task_dict['status'] = status.value  # Store the normalized state.
            serializable_tasks.append(task_dict)
            
        try:
            write_json_atomic(self.tasks_file, serializable_tasks)
        except Exception as e:
            log.error(f"작업 목록 저장 실패: {e}", exc_info=True)
    
    def load_tasks(self):
        """Load the saved task list."""
        if not os.path.exists(self.tasks_file):
            return []
            
        try:
            return valid_task_records(read_json(self.tasks_file))
        except Exception as e:
            log.error(f"작업 목록 불러오기 실패: {e}", exc_info=True)
            return []
