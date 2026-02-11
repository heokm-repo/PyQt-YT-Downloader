"""
작업 액션 클래스
개별 작업에 대한 액션(일시정지, 재개, 재시도, 파일 작업 등)을 담당
"""
import os
import subprocess
from typing import Optional, List, TYPE_CHECKING



from utils.logger import log
from constants import TaskStatus
from locales.strings import STR

if TYPE_CHECKING:
    from data.models import DownloadTask
    from gui.widgets.task_item import TaskWidget
    from core.scheduler import DownloadScheduler


class TaskActions:
    """
    작업 관련 액션을 처리하는 클래스
    
    Attributes:
        main_window: 메인 윈도우 참조 (tasks, task_widgets, scheduler 등 접근용)
    """
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    # --- 헬퍼 메서드 ---
    
    def _get_task(self, task_id: int) -> Optional['DownloadTask']:
        """task_id로 DownloadTask 객체 찾기"""
        return self.main_window.get_task_by_id(task_id)
    
    def _get_widget(self, task_id: int) -> Optional['TaskWidget']:
        """task_id로 TaskWidget 찾기"""
        return self.main_window.task_widgets.get(task_id)
    
    @property
    def _scheduler(self) -> 'DownloadScheduler':
        """스케줄러 접근"""
        return self.main_window.scheduler
    
    @property
    def _settings(self) -> dict:
        """현재 설정 접근"""
        return self.main_window.settings
    
    # --- 작업 제어 메서드 ---
    
    def pause_task(self, task_id: int) -> None:
        """개별 작업 일시 정지"""
        task = self._get_task(task_id)
        if not task:
            return
        
        if task.status == TaskStatus.DOWNLOADING:
            # 다운로드 중인 작업: 스케줄러에 일시정지 플래그 설정
            self._scheduler.pause_task(task_id)
            task.status = TaskStatus.PAUSED
            
            widget = self._get_widget(task_id)
            if widget:
                widget.set_paused()
            
        elif task.status == TaskStatus.WAITING:
            # 대기 중인 작업: 플래그만 설정
            self._scheduler.pause_task(task_id)
            task.status = TaskStatus.PAUSED
            
            widget = self._get_widget(task_id)
            if widget:
                widget.set_paused()
        
        self.main_window.update_progress_ui()

    def resume_task(self, task_id: int) -> None:
        """일시 정지된 작업을 이어받기"""
        task = self._get_task(task_id)
        if not task: 
            return
        
        # 스케줄러에서 일시정지 플래그 제거
        self._scheduler.resume_task(task_id)
        
        # 1. 상태 업데이트
        widget = self._get_widget(task_id)
        if widget:
            widget.set_status('waiting')
            widget.status_label.setText(STR.STATUS_WAITING_DOTS)
        
        task.status = TaskStatus.WAITING
        
        # 2. 큐에 작업 다시 추가 (저장된 settings와 meta 사용)
        settings = task.settings if task.settings else self._settings.copy()
        
        # 이어받기 플래그 추가 (덮어쓰기 방지)
        settings['is_resume'] = True
        
        meta = task.meta
        url = task.url
        
        if not meta or not url:
            # 데이터가 손상된 경우 재시도 로직으로 위임
            self.retry_task(task_id)
            return

        # 우선순위 1 (이어받기 작업)를 스케줄러에 추가
        self._scheduler.add_task(1, task_id, url, settings, meta)
        self.main_window.update_progress_ui()

    def retry_task(self, task_id: int) -> None:
        """다운로드 재시도"""
        task = self._get_task(task_id)
        if not task: 
            return

        url = task.url
        if not url:
            return
        
        # video_id가 있을 때만 중복 체크
        if task.video_id:
            current_settings = self.main_window.settings.copy()
            target_format = current_settings.get('format', 'mp4')
            
            # 중복 체크 (사용자 확인 포함)
            from data.managers import DuplicateChecker
            dup_checker = DuplicateChecker(
                self.main_window.history_manager,
                self.main_window
            )
            
            is_cancelled = dup_checker.check_duplicate(
                task.video_id, task_id, self.main_window.tasks[:], target_format
            )
            
            if is_cancelled:
                # 사용자가 재다운로드를 거부 -> 카드 유지
                return
            
            # 사용자가 Yes를 선택 -> history에서 제거하여 start_download에서 중복 체크 안뜨게 함
            self.main_window.history_manager.remove_from_history(task.video_id, target_format)
        
        # 기존 카드 제거 후 새로 다운로드
        self.main_window.remove_task_from_list(task_id)
        self.main_window.url_input.setText(url)
        self.main_window.start_download()
        
        self.main_window.update_progress_ui()

    # --- 파일 관련 액션 메서드 ---

    def copy_url(self, task_id: int) -> None:
        """작업 URL을 클립보드에 복사"""
        task = self._get_task(task_id)
        if task and task.url:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(task.url)
            log.info(f"URL 복사됨: {task.url}")
    
    def play_file(self, task_id: int) -> None:
        """파일 실행"""
        task = self._get_task(task_id)
        from gui.widgets.message_dialog import MessageDialog
        import constants
        
        if not task:
            MessageDialog(STR.TITLE_ERROR, STR.ERR_TASK_NOT_FOUND, 
                          MessageDialog.WARNING, self.main_window).exec_()
            return
        
        path = task.output_path
        if not path:
            MessageDialog(STR.TITLE_ERROR, STR.ERR_NO_FILE_PATH, 
                          MessageDialog.WARNING, self.main_window).exec_()
            return
        
        # 절대 경로로 변환 (PyInstaller 환경 대응)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        # 파일 존재 확인
        if os.path.exists(path) and os.path.isfile(path):
            try:
                os.startfile(path)
            except Exception as e:
                MessageDialog(STR.TITLE_ERROR, STR.ERR_EXECUTE_FILE.format(error=str(e)), 
                              MessageDialog.WARNING, self.main_window).exec_()
        else:
            MessageDialog(STR.TITLE_ERROR, 
                          STR.ERR_FILE_NOT_FOUND_PATH.format(path=path),
                          MessageDialog.WARNING, self.main_window).exec_()

    def open_folder(self, task_id: int) -> None:
        """파일이 있는 폴더 열기"""
        task = self._get_task(task_id)
        if task and task.output_path:
            path = os.path.abspath(task.output_path)
            if os.path.exists(path):
                try:
                    subprocess.Popen(f'explorer /select,"{path}"')
                except Exception as e:
                    from gui.widgets.message_dialog import MessageDialog
                    MessageDialog(STR.TITLE_ERROR, STR.ERR_OPEN_FOLDER.format(error=e), 
                                  MessageDialog.WARNING, self.main_window).exec_()
            else:
                folder = os.path.dirname(path)
                if os.path.exists(folder):
                    os.startfile(folder)

    def delete_file(self, task_id: int, confirm: bool = True) -> None:
        """파일 삭제 및 목록 제거"""
        task = self._get_task(task_id)
        if not task: 
            return
        
        from gui.widgets.message_dialog import MessageDialog
        from PyQt5.QtWidgets import QDialog

        if confirm:
            dialog = MessageDialog(STR.TITLE_DELETE_CONFIRM, 
                                   STR.MSG_DELETE_CONFIRM,
                                   MessageDialog.QUESTION, self.main_window, show_cancel=False)
            if dialog.exec_() != QDialog.Accepted:
                return

        output_path = task.output_path
        if output_path:
            # 절대 경로로 변환 (PyInstaller 환경 대응)
            if not os.path.isabs(output_path):
                output_path = os.path.abspath(output_path)
            
            # 파일 존재 및 파일 타입 확인
            if os.path.exists(output_path) and os.path.isfile(output_path):
                try:
                    os.remove(output_path)
                except PermissionError as e:
                    MessageDialog(
                        STR.TITLE_DELETE_FAILED, 
                        STR.ERR_DELETE_PERMISSION.format(path=str(e)),
                        MessageDialog.WARNING, self.main_window
                    ).exec_()
                    log.warning(f"파일 삭제 실패 (권한, task_id={task_id}): {e}")
                except Exception as e:
                    MessageDialog(STR.TITLE_DELETE_FAILED, STR.ERR_DELETE_ERROR.format(error=str(e)), 
                                  MessageDialog.WARNING, self.main_window).exec_()
                    log.error(f"파일 삭제 실패 (task_id={task_id}): {e}", exc_info=True)
            elif not os.path.exists(output_path):
                # 파일이 이미 없는 경우 경고 메시지 없이 목록에서만 제거
                log.debug(f"파일이 이미 존재하지 않음: {output_path}")

        self.main_window.remove_task_from_list(task_id)

    # --- 선택된 작업들에 대한 일괄 액션 ---

    def pause_selected(self, selected_ids: List[int]) -> None:
        """선택된 작업들 일시정지"""
        for task_id in selected_ids:
            task = self._get_task(task_id)
            if task and task.status in [TaskStatus.DOWNLOADING, TaskStatus.WAITING]:
                self.pause_task(task_id)
    
    def resume_selected(self, selected_ids: List[int]) -> None:
        """선택된 작업들 이어받기"""
        for task_id in selected_ids:
            task = self._get_task(task_id)
            if task and task.status == TaskStatus.PAUSED:
                self.resume_task(task_id)
    
    def retry_selected(self, selected_ids: List[int]) -> None:
        """선택된 작업들 재시도"""
        for task_id in selected_ids:
            task = self._get_task(task_id)
            if task and task.status == TaskStatus.FAILED:
                self.retry_task(task_id)
    
    def open_folders_for_selected(self, selected_ids: List[int]) -> None:
        """선택된 작업들의 폴더 열기"""
        opened_folders = set()
        for task_id in selected_ids:
            task = self._get_task(task_id)
            if task and task.output_path:
                folder = os.path.dirname(os.path.abspath(task.output_path))
                if folder not in opened_folders:
                    opened_folders.add(folder)
                    if os.path.exists(folder):
                        os.startfile(folder)
    
    def delete_files_for_selected(self, selected_ids: List[int], tasks: List['DownloadTask']) -> bool:
        """
        선택된 작업들의 파일 삭제
        
        Returns:
            bool: 삭제 진행 여부 (사용자가 취소하면 False)
        """
        count = len([t for t in tasks if t.id in selected_ids and t.status == TaskStatus.FINISHED])
        if count == 0:
            return False
        
        from gui.widgets.message_dialog import MessageDialog
        from PyQt5.QtWidgets import QDialog
        
        
        dialog = MessageDialog(STR.TITLE_DELETE_CONFIRM,
                               STR.MSG_DELETE_CONFIRM_MANY.format(count=count),
                               MessageDialog.QUESTION, self.main_window, show_cancel=False)
                               
        if dialog.exec_() != QDialog.Accepted:
            return False
        
        for task_id in selected_ids:
            task = self._get_task(task_id)
            if task and task.status == TaskStatus.FINISHED:
                self.delete_file(task_id, confirm=False)
        
        return True
    
    def remove_selected_from_list(self, selected_ids: List[int]) -> bool:
        """
        선택된 작업들을 목록에서 제거
        
        Returns:
            bool: 제거 진행 여부 (사용자가 취소하면 False)
        """
        count = len(selected_ids)
        if count == 0:
            return False
        
        if count > 1:
            from gui.widgets.message_dialog import MessageDialog
            from PyQt5.QtWidgets import QDialog
            
            
            dialog = MessageDialog(STR.TITLE_REMOVE_CONFIRM,
                                   STR.MSG_REMOVE_CONFIRM.format(count=count),
                                   MessageDialog.QUESTION, self.main_window, show_cancel=False)
                                   
            if dialog.exec_() != QDialog.Accepted:
                return False
        
        for task_id in selected_ids:
            self.main_window.remove_task_from_list(task_id)
        
        return True
