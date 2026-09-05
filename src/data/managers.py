"""Data managers for history and task-list persistence."""
import os
import json
import sqlite3
import datetime

from utils.utils import get_user_data_path
from utils.logger import log
from constants import (
    TaskStatus, DEFAULT_FORMAT,
    HISTORY_DB_FILENAME, TASKS_JSON_FILENAME, HISTORY_TABLE_NAME, DATE_FORMAT
)
from locales.strings import STR
from data.models import DownloadTask
from data.task_validation import valid_task_records


class HistoryManager:
    """SQLite-backed download history manager."""
    
    def __init__(self):
        # Use a SQLite database file.
        self.db_path = os.path.join(get_user_data_path(), HISTORY_DB_FILENAME)
        self._init_db()
    
    def _init_db(self):
        """Initialize and migrate database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Use extractor, ID, and format extension as the composite key.
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {HISTORY_TABLE_NAME} (
                        extractor TEXT,
                        video_id TEXT,
                        format TEXT,
                        title TEXT,
                        uploader TEXT,
                        download_date TEXT,
                        PRIMARY KEY (extractor, video_id, format)
                    )
                ''')
                conn.commit()
                
                # Migrate old databases that do not have an extractor column.
                self._migrate_db(conn)
        except Exception as e:
            log.error(f"DB 초기화 오류: {e}", exc_info=True)
    
    def _migrate_db(self, conn):
        """Add the extractor column to old databases and fill existing rows with youtube."""
        try:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({HISTORY_TABLE_NAME})")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'extractor' not in columns:
                log.info("DB 마이그레이션: extractor 컬럼 추가 중...")
                # 1. Back up the existing table.
                cursor.execute(f"ALTER TABLE {HISTORY_TABLE_NAME} RENAME TO {HISTORY_TABLE_NAME}_old")
                # 2. Create the table with the new schema.
                cursor.execute(f'''
                    CREATE TABLE {HISTORY_TABLE_NAME} (
                        extractor TEXT,
                        video_id TEXT,
                        format TEXT,
                        title TEXT,
                        uploader TEXT,
                        download_date TEXT,
                        PRIMARY KEY (extractor, video_id, format)
                    )
                ''')
                # 3. Copy existing data with extractor="youtube".
                cursor.execute(f'''
                    INSERT INTO {HISTORY_TABLE_NAME} (extractor, video_id, format, title, uploader, download_date)
                    SELECT 'youtube', video_id, format, title, uploader, download_date
                    FROM {HISTORY_TABLE_NAME}_old
                ''')
                # 4. Drop the backup table.
                cursor.execute(f"DROP TABLE {HISTORY_TABLE_NAME}_old")
                conn.commit()
                log.info("DB 마이그레이션 완료")
        except Exception as e:
            log.error(f"DB 마이그레이션 오류: {e}", exc_info=True)
    
    def is_downloaded(self, extractor, video_id, fmt):
        """Return whether a video was downloaded for a specific extractor and format."""
        if not video_id:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT 1 FROM {HISTORY_TABLE_NAME} WHERE extractor = ? AND video_id = ? AND format = ?", 
                    (extractor, video_id, fmt)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            log.error(f"DB 검색 오류 (extractor={extractor}, video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
            return False
    
    def add_to_history(self, extractor, video_id, meta, fmt=DEFAULT_FORMAT):
        """Add a record to history."""
        if not video_id:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # INSERT OR REPLACE overwrites existing rows.
                cursor.execute(
                    f"INSERT OR REPLACE INTO {HISTORY_TABLE_NAME} VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        extractor,
                        video_id, 
                        fmt, 
                        meta.get('title', ''), 
                        meta.get('uploader', ''),
                        datetime.datetime.now().strftime(DATE_FORMAT)
                    )
                )
                conn.commit()
        except Exception as e:
            log.error(f"DB 저장 오류 (extractor={extractor}, video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
    
    def remove_from_history(self, extractor, video_id, fmt=DEFAULT_FORMAT):
        """Remove a record, used by retry flows."""
        if not video_id:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM {HISTORY_TABLE_NAME} WHERE extractor = ? AND video_id = ? AND format = ?",
                    (extractor, video_id, fmt)
                )
                conn.commit()
                log.info(f"Removed from history: {extractor}/{video_id} (format={fmt})")
        except Exception as e:
            log.error(f"DB 삭제 오류 (extractor={extractor}, video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
    
class TaskManager:
    """Manage the saved task list."""
    
    def __init__(self):
        self.tasks_file = os.path.join(get_user_data_path(), TASKS_JSON_FILENAME)
    
    def save_tasks(self, tasks: list[DownloadTask]):
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
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"작업 목록 저장 실패: {e}", exc_info=True)
    
    def load_tasks(self):
        """Load the saved task list."""
        if not os.path.exists(self.tasks_file):
            return []
            
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return valid_task_records(json.load(f))
        except Exception as e:
            log.error(f"작업 목록 불러오기 실패: {e}", exc_info=True)
            return []


class DuplicateChecker:
    """Duplicate download checker that includes extractor and extension."""
    
    def __init__(self, history_manager):
        self.history_manager = history_manager
    
    def is_duplicate(self, extractor, video_id, current_task_id, tasks: list[DownloadTask], target_ext=DEFAULT_FORMAT):
        """
        Check whether a download would be a duplicate without UI side effects.
        
        Args:
            extractor: Site extractor identifier.
            video_id: Video ID.
            current_task_id: Current task ID.
            tasks: Task list.
            target_ext: Target extension, defaulting to mp4.
        
        Returns:
            Tuple of duplicate flag, duplicate message, and duplicate task.
        """
        # 1. Check history by extractor and extension.
        is_in_history = self.history_manager.is_downloaded(extractor, video_id, target_ext)
        
        # 2. Check the current queue by extractor and extension.
        is_in_queue = False
        duplicate_task = None
        for task in tasks:
            # Ignore the current task itself.
            if task.id == current_task_id:
                continue
            
            # Infer each queued task extension from settings.
            task_ext = task.settings.get('format', DEFAULT_FORMAT)
            
            if task.extractor == extractor and task.video_id == video_id and task_ext == target_ext:
                if task.is_active():
                    is_in_queue = True
                    duplicate_task = task
                    break
        
        # A duplicate was found.
        if is_in_history or is_in_queue:
            # Build the message.
            message = STR.MSG_DUP_ALREADY_DONE.format(format=target_ext)
            if is_in_queue and duplicate_task:
                status_text = {
                    TaskStatus.WAITING: STR.STATUS_WAITING_DOTS,
                    TaskStatus.DOWNLOADING: STR.STATUS_DOWNLOADING_DOTS,
                    TaskStatus.PAUSED: STR.STATUS_PAUSED
                }.get(duplicate_task.status, STR.STATUS_IN_PROGRESS)
                message += STR.MSG_DUP_IN_QUEUE.format(status=status_text)
            message += STR.MSG_DUP_ASK_OVERWRITE
            
            return True, message, duplicate_task
        
        # Return False when no duplicate was found.
        return False, None, None
