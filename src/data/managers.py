"""
데이터 관리 클래스
히스토리 및 작업 목록 관리
"""
import os
import json
import sqlite3
import datetime
from PyQt5.QtWidgets import QDialog

from utils.utils import get_user_data_path
from utils.logger import log
from constants import (
    TaskStatus, DEFAULT_FORMAT,
    HISTORY_DB_FILENAME, TASKS_JSON_FILENAME, HISTORY_TABLE_NAME, DATE_FORMAT
)
from locales.strings import STR
from data.models import DownloadTask


class HistoryManager:
    """SQLite 기반 다운로드 히스토리 관리"""
    
    def __init__(self):
        # SQLite DB 파일 사용
        self.db_path = os.path.join(get_user_data_path(), HISTORY_DB_FILENAME)
        self._init_db()
    
    def _init_db(self):
        """DB 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # ID와 포맷(확장자)를 복합 키로 설정
                cursor.execute(f'''
                    CREATE TABLE IF NOT EXISTS {HISTORY_TABLE_NAME} (
                        video_id TEXT,
                        format TEXT,
                        title TEXT,
                        uploader TEXT,
                        download_date TEXT,
                        PRIMARY KEY (video_id, format)
                    )
                ''')
                conn.commit()
        except Exception as e:
            log.error(f"DB 초기화 오류: {e}", exc_info=True)
    
    def is_downloaded(self, video_id, fmt):
        """특정 포맷으로 다운로드 여부 확인"""
        if not video_id:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT 1 FROM {HISTORY_TABLE_NAME} WHERE video_id = ? AND format = ?", 
                    (video_id, fmt)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            log.error(f"DB 검색 오류 (video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
            return False
    
    def add_to_history(self, video_id, meta, fmt=DEFAULT_FORMAT):
        """기록 추가"""
        if not video_id:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # INSERT OR REPLACE: 이미 있으면 덮어쓰기
                cursor.execute(
                    f"INSERT OR REPLACE INTO {HISTORY_TABLE_NAME} VALUES (?, ?, ?, ?, ?)",
                    (
                        video_id, 
                        fmt, 
                        meta.get('title', ''), 
                        meta.get('uploader', ''),
                        datetime.datetime.now().strftime(DATE_FORMAT)
                    )
                )
                conn.commit()
        except Exception as e:
            log.error(f"DB 저장 오류 (video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
    
    def remove_from_history(self, video_id, fmt=DEFAULT_FORMAT):
        """기록 제거 (retry 시 사용)"""
        if not video_id:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"DELETE FROM {HISTORY_TABLE_NAME} WHERE video_id = ? AND format = ?",
                    (video_id, fmt)
                )
                conn.commit()
                log.info(f"Removed from history: {video_id} (format={fmt})")
        except Exception as e:
            log.error(f"DB 삭제 오류 (video_id={video_id}, fmt={fmt}): {e}", exc_info=True)
    
    # 하위 호환성을 위한 메서드 (기존 코드에서 사용 중일 수 있음)
    def is_video_downloaded(self, video_id):
        """다운로드 히스토리에 있는지 확인 (확장자 무관) - 하위 호환성"""
        if not video_id:
            return False
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    f"SELECT 1 FROM {HISTORY_TABLE_NAME} WHERE video_id = ? LIMIT 1", 
                    (video_id,)
                )
                return cursor.fetchone() is not None
        except Exception as e:
            log.error(f"DB 검색 오류 (video_id={video_id}): {e}", exc_info=True)
            return False


class TaskManager:
    """작업 목록 관리"""
    
    def __init__(self):
        self.tasks_file = os.path.join(get_user_data_path(), TASKS_JSON_FILENAME)
    
    def save_tasks(self, tasks: list[DownloadTask]):
        """현재 작업 목록을 JSON 파일로 저장"""
        serializable_tasks = []
        for task in tasks:
            # 상태 보정: 다운로드 중이거나 대기 중인 항목은 'Paused'로 저장하여
            # 다음 실행 시 자동으로 시작되지 않게 함 (렉 방지 및 사용자 제어권)
            status = task.status
            if status in [TaskStatus.DOWNLOADING, TaskStatus.WAITING]:
                status = TaskStatus.PAUSED
            
            # DownloadTask를 딕셔너리로 변환
            task_dict = task.to_dict()
            task_dict['status'] = status.value  # 보정된 상태로 저장
            serializable_tasks.append(task_dict)
            
        try:
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"작업 목록 저장 실패: {e}", exc_info=True)
    
    def load_tasks(self):
        """저장된 작업 목록 불러오기"""
        if not os.path.exists(self.tasks_file):
            return []
            
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"작업 목록 불러오기 실패: {e}", exc_info=True)
            return []


class DuplicateChecker:
    """중복 다운로드 체크 (확장자 포함)"""
    
    def __init__(self, history_manager, parent_widget=None):
        self.history_manager = history_manager
        self.parent_widget = parent_widget
    
    def is_duplicate(self, video_id, current_task_id, tasks: list[DownloadTask], target_ext=DEFAULT_FORMAT):
        """
        중복 다운로드 여부 확인 (순수 로직, UI 없음)
        
        Args:
            video_id: 비디오 ID
            current_task_id: 현재 작업 ID
            tasks: 작업 목록 (DownloadTask 리스트)
            target_ext: 대상 확장자 (기본값: 'mp4')
        
        Returns:
            tuple: (중복 여부, 중복 메시지, 중복된 작업)
                - 중복 여부: bool
                - 중복 메시지: str (중복이 없으면 None)
                - 중복된 작업: DownloadTask (중복이 없으면 None)
        """
        # 1. 히스토리 확인 (DB 조회 - 확장자 포함)
        is_in_history = self.history_manager.is_downloaded(video_id, target_ext)
        
        # 2. 현재 큐 확인 (확장자 포함)
        is_in_queue = False
        duplicate_task = None
        for task in tasks:
            # 현재 작업 자신은 제외
            if task.id == current_task_id:
                continue
            
            # 큐에 있는 작업의 확장자 확인 (settings에서 유추)
            task_ext = task.settings.get('format', DEFAULT_FORMAT)
            
            if task.video_id == video_id and task_ext == target_ext:
                if task.is_active():
                    is_in_queue = True
                    duplicate_task = task
                    break
        
        # 중복이 발견된 경우
        if is_in_history or is_in_queue:
            # 메시지 구성
            message = STR.MSG_DUP_ALREADY_DONE.format(format=target_ext)
            if is_in_queue and duplicate_task:
                status_text = {
                    TaskStatus.WAITING: STR.STATUS_WAITING,
                    TaskStatus.DOWNLOADING: STR.STATUS_DOWNLOADING,
                    TaskStatus.PAUSED: STR.STATUS_PAUSED
                }.get(duplicate_task.status, STR.STATUS_IN_PROGRESS)
                message += STR.MSG_DUP_IN_QUEUE.format(status=status_text)
            message += STR.MSG_DUP_ASK_OVERWRITE
            
            return True, message, duplicate_task
        
        # 중복이 없으면 False 반환
        return False, None, None
    
    def check_duplicate(self, video_id, current_task_id, tasks: list[DownloadTask], target_ext=DEFAULT_FORMAT):
        """
        중복 다운로드 체크 (확장자 포함) + UI 확인
        - 같은 ID라도 확장자가 다르면 OK
        - 같은 ID이고 확장자도 같으면 경고
        
        Args:
            video_id: 비디오 ID
            current_task_id: 현재 작업 ID
            tasks: 작업 목록 (DownloadTask 리스트)
            target_ext: 대상 확장자 (기본값: 'mp4')
        
        Returns:
            bool: True면 중복으로 간주하여 취소, False면 다운로드 진행
        """
        is_dup, message, duplicate_task = self.is_duplicate(
            video_id, current_task_id, tasks, target_ext
        )
        
        if not is_dup:
            return False
        
        # 확인 대화상자 표시
        from gui.widgets.message_dialog import MessageDialog
        
        dialog = MessageDialog(STR.DLG_DUP_CHECK_TITLE, message, 
                               MessageDialog.QUESTION, self.parent_widget, show_cancel=False)
        
        # 사용자가 "아니요"를 선택한 경우 (Reject) True 반환 (중복 취소)
        # MessageDialog의 QUESTION 타입은 
        # Yes -> accept -> Accepted
        # No -> reject -> Rejected
        
        return dialog.exec_() != QDialog.Accepted
