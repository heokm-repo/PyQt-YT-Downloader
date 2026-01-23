"""
작업 액션 클래스
개별 작업에 대한 액션(일시정지, 재개, 재시도, 파일 작업 등)을 담당
"""
import os
import subprocess
from typing import Optional, List, TYPE_CHECKING

from PyQt5.QtWidgets import QMessageBox

from logger import log
from constants import TaskStatus

if TYPE_CHECKING:
    from models import DownloadTask
    from ui.task_item import TaskWidget
    from scheduler import DownloadScheduler


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
            widget.status_label.setText("대기 중...")
        
        task.status = TaskStatus.WAITING
        
        # 2. 큐에 작업 다시 추가 (저장된 settings와 meta 사용)
        settings = task.settings if task.settings else self._settings.copy()
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

        self.main_window.remove_task_from_list(task_id)
        
        url = task.url
        if url:
            self.main_window.url_input.setText(url)
            self.main_window.start_download()
        
        self.main_window.update_progress_ui()

    # --- 파일 관련 액션 메서드 ---

    def play_file(self, task_id: int) -> None:
        """파일 실행"""
        task = self._get_task(task_id)
        if not task:
            QMessageBox.warning(self.main_window, "오류", "작업을 찾을 수 없습니다.")
            return
        
        path = task.output_path
        if not path:
            QMessageBox.warning(self.main_window, "오류", "파일 경로가 저장되지 않았습니다.")
            return
        
        # 절대 경로로 변환 (PyInstaller 환경 대응)
        if not os.path.isabs(path):
            path = os.path.abspath(path)
        
        # 파일 존재 확인
        if os.path.exists(path) and os.path.isfile(path):
            try:
                os.startfile(path)
            except Exception as e:
                QMessageBox.warning(self.main_window, "오류", f"파일을 실행할 수 없습니다:\n{str(e)}")
        else:
            QMessageBox.warning(self.main_window, "오류", 
                              f"파일을 찾을 수 없습니다.\n\n경로: {path}\n\n"
                              f"파일이 이동되었거나 삭제되었을 수 있습니다.")

    def open_folder(self, task_id: int) -> None:
        """파일이 있는 폴더 열기"""
        task = self._get_task(task_id)
        if task and task.output_path:
            path = os.path.abspath(task.output_path)
            if os.path.exists(path):
                try:
                    subprocess.Popen(f'explorer /select,"{path}"')
                except Exception as e:
                    QMessageBox.warning(self.main_window, "오류", f"폴더를 열 수 없습니다: {e}")
            else:
                folder = os.path.dirname(path)
                if os.path.exists(folder):
                    os.startfile(folder)

    def delete_file(self, task_id: int, confirm: bool = True) -> None:
        """파일 삭제 및 목록 제거"""
        task = self._get_task(task_id)
        if not task: 
            return

        if confirm:
            reply = QMessageBox.question(
                self.main_window, '삭제 확인', 
                '파일을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
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
                    QMessageBox.warning(
                        self.main_window, "삭제 실패", 
                        f"파일이 사용 중이거나 권한이 없습니다:\n{str(e)}\n\n"
                        f"파일이 다른 프로그램에서 열려있는지 확인해주세요."
                    )
                    log.warning(f"파일 삭제 실패 (권한, task_id={task_id}): {e}")
                except Exception as e:
                    QMessageBox.warning(self.main_window, "삭제 실패", f"파일을 삭제할 수 없습니다:\n{str(e)}")
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
        
        reply = QMessageBox.question(
            self.main_window, '삭제 확인',
            f'{count}개의 파일을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.No:
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
            reply = QMessageBox.question(
                self.main_window, '제거 확인',
                f'{count}개의 항목을 목록에서 제거하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False
        
        for task_id in selected_ids:
            self.main_window.remove_task_from_list(task_id)
        
        return True
