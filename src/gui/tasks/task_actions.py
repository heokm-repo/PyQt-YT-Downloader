"""Actions for individual tasks, including pause, resume, retry, and file operations."""
import os
from typing import Optional, List, TYPE_CHECKING

from utils.logger import log
from utils.url_security import redact_url_for_log
from constants import TaskStatus
from locales.strings import STR
from gui.dialogs.messages import ask_question, show_warning
from gui.tasks.task_action_state import (
    is_pausable_status,
    is_resumable_status,
    is_retryable_status,
)
from gui.tasks.task_bulk_action_plan import (
    build_delete_files_plan,
    build_remove_completed_plan,
    build_remove_selected_plan,
    folders_to_open_for_selected,
)
from gui.tasks.task_file_delete import DeleteFileStatus, delete_output_file
from gui.tasks.task_file_open import (
    OpenFileStatus,
    OpenFolderStatus,
    open_output_file,
    open_output_folder,
)
from gui.tasks.task_resume_plan import build_resume_task_plan
from gui.tasks.task_retry_plan import (
    build_retry_task_plan,
    should_continue_retry_after_duplicate_check,
)
from gui.tasks.task_selection_plan import (
    selected_task_ids_matching,
)

if TYPE_CHECKING:
    from data.models import DownloadTask
    from gui.widgets.task_item import TaskWidget
    from core.scheduler import DownloadScheduler


class TaskActions:
    """Handle task-related actions through the main window reference."""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    # --- Helper Methods ---
    
    def _get_task(self, task_id: int) -> Optional['DownloadTask']:
        """Find a DownloadTask by task_id."""
        return self.main_window.get_task_by_id(task_id)
    
    def _get_widget(self, task_id: int) -> Optional['TaskWidget']:
        """Find a TaskWidget by task_id."""
        return self.main_window.task_widgets.get(task_id)
    
    @property
    def _scheduler(self) -> 'DownloadScheduler':
        """Return the scheduler."""
        return self.main_window.scheduler
    
    @property
    def _settings(self) -> dict:
        """Return current settings."""
        return self.main_window.settings

    def _confirm_question(self, title: str, message: str) -> bool:
        """Show a question dialog and return True when accepted."""
        return ask_question(self.main_window, title, message)

    def _show_warning(self, title: str, message: str) -> None:
        """Show a warning dialog."""
        show_warning(self.main_window, title, message)

    # --- Task Control Methods ---
    
    def pause_task(self, task_id: int) -> None:
        """Pause a single waiting or downloading task."""
        task = self._get_task(task_id)
        if not task:
            return
        
        if is_pausable_status(task.status):
            self._scheduler.pause_task(task_id)
            task.status = TaskStatus.PAUSED
            
            widget = self._get_widget(task_id)
            if widget:
                widget.set_paused()
        
        self.main_window.update_progress_ui()

    def resume_task(self, task_id: int) -> None:
        """Resume a paused task."""
        task = self._get_task(task_id)
        if not task: 
            return
        
        was_individually_paused = self._scheduler.is_task_paused(task_id)
        
        # If the global toggle is stopped, resume it for user convenience.
        if not self.main_window.toggle_enabled:
            self.main_window.toggle_download()
            if task.status == TaskStatus.WAITING:
                self.main_window.update_progress_ui()
                return
            if not was_individually_paused:
                return
        
        self._scheduler.resume_task(task_id)
        
        # 1. Update state.
        widget = self._get_widget(task_id)
        if widget:
            widget.set_status('waiting')
            widget.status_label.setText(STR.STATUS_WAITING_DOTS)
        
        task.status = TaskStatus.WAITING
        
        # 2. Requeue the task with its saved settings and metadata.
        resume_plan = build_resume_task_plan(task, self._settings)
        if not resume_plan:
            # Delegate corrupted data cases to the retry flow.
            self.retry_task(task_id)
            return

        # Add the resume task to the scheduler with priority 1.
        self._scheduler.add_task(
            1,
            task_id,
            resume_plan.url,
            resume_plan.settings,
            resume_plan.meta,
            is_resume=True,
        )
        self.main_window.update_progress_ui()

    def retry_task(self, task_id: int) -> None:
        """Resume a failed task, or redownload a completed task."""
        if not self.main_window.toggle_enabled:
            self.main_window.toggle_download()

        task = self._get_task(task_id)
        if task and task.status == TaskStatus.FAILED:
            resume_plan = build_resume_task_plan(task, self._settings)
            if not resume_plan:
                return

            self._scheduler.resume_task(task_id)
            task.status = TaskStatus.WAITING

            widget = self._get_widget(task_id)
            if widget:
                widget.set_status('waiting')
                widget.status_label.setText(STR.STATUS_WAITING_DOTS)

            self._scheduler.add_task(
                1,
                task_id,
                resume_plan.url,
                resume_plan.settings,
                resume_plan.meta,
                is_resume=True,
            )
            self.main_window.update_progress_ui()
            return

        plan = build_retry_task_plan(task, self.main_window.settings)
        if not plan:
            return

        if not should_continue_retry_after_duplicate_check(
            plan.duplicate_target,
            task_id,
            self.main_window.tasks[:],
            self.main_window.history_manager,
            self.main_window,
        ):
            return

        self.main_window.remove_task_from_list(task_id, discard_workspace=False)
        self.main_window.url_input.setText(plan.url)
        self.main_window.start_download()

        self.main_window.update_progress_ui()

    # --- File Action Methods ---

    def copy_url(self, task_id: int) -> None:
        """Copy a task URL to the clipboard."""
        task = self._get_task(task_id)
        if task and task.url:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(task.url)
            log.info(f"URL 복사됨: {redact_url_for_log(task.url)}")
    
    def play_file(self, task_id: int) -> None:
        """Open a downloaded file."""
        task = self._get_task(task_id)
        if not task:
            self._show_warning(STR.TITLE_ERROR, STR.ERR_TASK_NOT_FOUND)
            return

        result = open_output_file(task.output_path)
        if result.status == OpenFileStatus.NO_PATH:
            self._show_warning(STR.TITLE_ERROR, STR.ERR_NO_FILE_PATH)
        elif result.status == OpenFileStatus.MISSING:
            self._show_warning(
                STR.TITLE_ERROR,
                STR.ERR_FILE_NOT_FOUND_PATH.format(path=result.output_path),
            )
        elif result.status == OpenFileStatus.ERROR:
            self._show_warning(
                STR.TITLE_ERROR,
                STR.ERR_EXECUTE_FILE.format(error=str(result.error)),
            )

    def open_folder(self, task_id: int) -> None:
        """Open the folder containing a downloaded file."""
        task = self._get_task(task_id)
        if not task:
            return

        result = open_output_folder(task.output_path)
        if result.status == OpenFolderStatus.ERROR:
            self._show_warning(
                STR.TITLE_ERROR,
                STR.ERR_OPEN_FOLDER.format(error=result.error),
            )

    def delete_file(self, task_id: int, confirm: bool = True) -> None:
        """Delete a downloaded file and remove its task from the list."""
        task = self._get_task(task_id)
        if not task:
            return

        if confirm and not self._confirm_question(
            STR.TITLE_DELETE_CONFIRM,
            STR.MSG_DELETE_CONFIRM,
        ):
            return

        result = delete_output_file(task.output_path)
        if result.status == DeleteFileStatus.PERMISSION_ERROR:
            error_text = str(result.error) if result.error else result.file_path
            self._show_warning(
                STR.TITLE_DELETE_FAILED,
                STR.ERR_DELETE_PERMISSION.format(path=error_text),
            )
            log.warning(
                f"File delete failed due to permission (task_id={task_id}): {error_text}"
            )
        elif result.status == DeleteFileStatus.ERROR:
            error_text = str(result.error) if result.error else result.file_path
            self._show_warning(
                STR.TITLE_DELETE_FAILED,
                STR.ERR_DELETE_ERROR.format(error=error_text),
            )
            log.error(
                f"File delete failed (task_id={task_id}): {error_text}",
                exc_info=result.exc_info,
            )
        elif result.status == DeleteFileStatus.MISSING:
            log.debug(f"File already missing: {result.output_path}")

        self.main_window.remove_task_from_list(task_id)

    # --- Bulk Actions For Selected Tasks ---

    def pause_selected(self, selected_ids: List[int]) -> None:
        """Pause selected pausable tasks."""
        for task_id in selected_task_ids_matching(
            selected_ids,
            self.main_window.tasks,
            lambda task: is_pausable_status(task.status),
        ):
            self.pause_task(task_id)
    
    def resume_selected(self, selected_ids: List[int]) -> None:
        """Resume selected paused tasks."""
        for task_id in selected_task_ids_matching(
            selected_ids,
            self.main_window.tasks,
            lambda task: is_resumable_status(task.status),
        ):
            self.resume_task(task_id)
    
    def retry_selected(self, selected_ids: List[int]) -> None:
        """Retry selected failed or finished tasks."""
        for task_id in selected_task_ids_matching(
            selected_ids,
            self.main_window.tasks,
            lambda task: is_retryable_status(task.status),
        ):
            self.retry_task(task_id)
    
    def open_folders_for_selected(self, selected_ids: List[int]) -> None:
        """Open folders for selected tasks."""
        for folder in folders_to_open_for_selected(selected_ids, self.main_window.tasks):
            os.startfile(folder)
    
    def delete_files_for_selected(self, selected_ids: List[int], tasks: List['DownloadTask']) -> bool:
        """
        Delete files for selected tasks.
        
        Returns:
            True if deletion proceeded, or False if the user cancelled.
        """
        plan = build_delete_files_plan(selected_ids, tasks)
        if not plan.has_tasks:
            return False
        
        if plan.needs_confirmation and not self._confirm_question(
            STR.TITLE_DELETE_CONFIRM,
            STR.MSG_DELETE_CONFIRM_MANY.format(count=plan.count),
        ):
            return False
        
        for task_id in plan.task_ids:
            self.delete_file(task_id, confirm=False)
        
        return True
    
    def remove_selected_from_list(self, selected_ids: List[int]) -> bool:
        """
        Remove selected tasks from the list.
        
        Returns:
            True if removal proceeded, or False if the user cancelled.
        """
        plan = build_remove_selected_plan(selected_ids)
        if not plan.has_tasks:
            return False
        
        if plan.needs_confirmation:
            if not self._confirm_question(
                STR.TITLE_REMOVE_CONFIRM,
                STR.MSG_REMOVE_CONFIRM.format(count=plan.count),
            ):
                return False
        
        for task_id in plan.task_ids:
            self.main_window.remove_task_from_list(task_id)
        
        return True

    def remove_all_completed_from_list(self) -> bool:
        """Remove all completed tasks from the list."""
        plan = build_remove_completed_plan(self.main_window.tasks)
        if not plan.has_tasks:
            return False
        
        if plan.needs_confirmation:
            if not self._confirm_question(
                STR.TITLE_REMOVE_CONFIRM,
                STR.MSG_REMOVE_COMPLETED_CONFIRM.format(count=plan.count),
            ):
                return False
                
        for task_id in plan.task_ids:
            self.main_window.remove_task_from_list(task_id)
            
        return True
