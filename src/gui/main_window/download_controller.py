"""Coordinate URL review, playlist analysis and download registration."""
from typing import Optional

from PyQt5.QtCore import QObject, QTimer, pyqtSlot
from PyQt5.QtWidgets import QApplication

from constants import WORKER_TERMINATE_WAIT_MS
from core.playlist_filter import filter_duplicate_videos
from core.url_processor import UrlProcessor
from core.workers import PlaylistAnalysisWorker
from gui.dialogs.main_window_messages import (
    ask_duplicate_confirmation_dialog, ask_playlist_video_preference,
    confirm_duplicate_overwrite_dialog, show_invalid_url_dialog,
    show_no_new_videos_dialog, show_playlist_error_dialog,
)
from gui.dialogs.messages import show_error
from gui.main_window.view_state import set_url_entry_enabled
from gui.main_window.worker_lifecycle import stop_running_worker
from gui.tasks.active_duplicate_replacement import wait_for_task_stop
from gui.tasks.duplicate_check_target import duplicate_target_format
from gui.tasks.playlist_registration import build_playlist_registration_decision
from gui.tasks.playlist_task_plan import build_playlist_task_plans
from gui.tasks.single_video_download import build_single_video_download_plan, review_single_video_duplicate
from locales.strings import STR
from utils.logger import log


class DownloadController(QObject):
    def __init__(self, window, task_list):
        super().__init__(window if isinstance(window, QObject) else None)
        self.window = window
        self.task_list = task_list
        self.playlist_worker = None
        self.pending_replacements = {}

    def _handle_playlist_download(self, clean_url: str):
        """Start playlist analysis after stopping any previous analysis worker."""
        if self.task_list.closed:
            return
        worker_stop = stop_running_worker(self.playlist_worker, WORKER_TERMINATE_WAIT_MS)
        if worker_stop.timed_out:
            log.warning("Previous playlist worker did not stop before timeout.")
            return

        self.window.status_label.setText(STR.MSG_ANALYZING_PLAYLIST)
        set_url_entry_enabled(self.window.url_input, self.window.download_btn, False)

        self.playlist_worker = PlaylistAnalysisWorker(clean_url, self.window)
        self.playlist_worker.analysis_finished.connect(self.window.on_playlist_analysis_finished)
        self.playlist_worker.finished.connect(self._on_playlist_finished)
        self.playlist_worker.start()

    @pyqtSlot()
    def _on_playlist_finished(self):
        worker = self.sender()
        if worker is self.playlist_worker:
            self.playlist_worker = None
            if not self.task_list.closed:
                set_url_entry_enabled(self.window.url_input, self.window.download_btn, True)
        worker.deleteLater()

    def _handle_single_video_download(self, clean_url: str, video_id: Optional[str], extractor: str = "unknown"):
        """Handle registration for a single video download."""
        if self.task_list.closed:
            return
        plan = build_single_video_download_plan(
            clean_url,
            video_id,
            extractor,
            self.window.settings,
        )

        duplicate_decision = review_single_video_duplicate(
            self.window.duplicate_checker,
            plan.duplicate_target,
            self.window.tasks.snapshot(),
            lambda message: confirm_duplicate_overwrite_dialog(
                self.window,
                STR.MSG_DUPLICATE_CHECK,
                message,
            ),
        )
        if self.task_list.closed:
            return
        if duplicate_decision.cancelled:
            self.window.status_label.setText(STR.MSG_DL_CANCELLED)
            return

        if duplicate_decision.duplicate_task is not None:
            self._replace_active_duplicate(
                duplicate_decision.duplicate_task,
                plan,
            )
            return

        self._register_single_video_plan(plan)

    def _register_single_video_plan(self, plan):
        """Register a reviewed single-video plan."""
        if self.task_list.closed:
            return
        with self.task_list.batch():
            self.window.total_tasks_in_queue += 1
            task_id = self.window.total_tasks_in_queue
            self.window._create_and_register_task(
                task_id,
                plan.clean_url,
                plan.video_id,
                plan.extractor,
            )

            self.window.status_label.setText(STR.MSG_ADDED_QUEUE)
            self.window.update_progress_ui()

    def _replace_active_duplicate(self, duplicate_task, plan):
        """Cancel an active duplicate and replace it only after it stops."""
        if self.task_list.closed:
            return
        task_id = duplicate_task.id
        if task_id in self.pending_replacements:
            self.window.status_label.setText(STR.MSG_DL_CANCELLED)
            return

        pending = (duplicate_task, plan)
        self.pending_replacements[task_id] = pending
        self.window.scheduler.cancel_task(task_id)

        def finalize_replacement():
            if self.task_list.closed or self.pending_replacements.get(task_id) != pending:
                return
            self.pending_replacements.pop(task_id, None)
            if self.window.get_task_by_id(task_id) is not duplicate_task:
                return
            with self.task_list.batch():
                self.window.remove_task_from_list(task_id)
                self._register_single_video_plan(plan)

        def replacement_timeout():
            if self.task_list.closed or self.pending_replacements.get(task_id) != pending:
                return
            self.pending_replacements.pop(task_id, None)
            self.window.status_label.setText(STR.MSG_DL_CANCELLED)
            show_error(
                self.window,
                STR.TITLE_ERROR,
                STR.ERR_DUPLICATE_REPLACEMENT_TIMEOUT,
            )

        QTimer.singleShot(
            0,
            lambda: wait_for_task_stop(
                self.window.scheduler,
                task_id,
                QTimer.singleShot,
                finalize_replacement,
                replacement_timeout,
            ),
        )

    def start_download(self):
        """Orchestrate download start."""
        if self.task_list.closed:
            return
        url = self.window.url_input.text().strip()
        prefer_playlist = False

        if UrlProcessor.requires_playlist_preference(url):
            preference = ask_playlist_video_preference(
                self.window,
                STR.TITLE_CHOICE,
                STR.MSG_CHOICE_PLAYLIST,
                STR.BTN_CHOICE_ALL,
                STR.BTN_CHOICE_VIDEO,
                STR.BTN_CANCEL,
            )
            if preference is None:
                return
            prefer_playlist = preference

        # Process and validate the URL.
        if self.task_list.closed:
            return
        result = UrlProcessor.process_url(url, prefer_playlist=prefer_playlist)
        if not result:
            show_invalid_url_dialog(self.window, STR.TITLE_ERROR, STR.ERR_INVALID_URL)
            return

        self.window.url_input.clear()
        self.window._show_task_list()

        # Branch between playlist and single-video handling.
        if result.is_playlist:
            self._handle_playlist_download(result.clean_url)
        else:
            self._handle_single_video_download(result.clean_url, result.video_id, result.extractor or 'unknown')

    def _enable_url_input(self):
        """Enable URL entry controls after playlist analysis."""
        set_url_entry_enabled(self.window.url_input, self.window.download_btn, True)

    def _handle_playlist_error(self, error_msg: str):
        """Show playlist errors and return the status bar to ready."""
        show_playlist_error_dialog(
            self.window,
            STR.TITLE_ERROR,
            error_msg,
            STR.ERR_PLAYLIST_FETCH,
        )
        self.window.status_label.setText(STR.MSG_READY)

    def _filter_duplicate_videos(self, video_ids: list, extractor: str = "youtube") -> tuple[list, int]:
        """Filter already downloaded or queued playlist videos."""
        return filter_duplicate_videos(
            video_ids,
            self.window.history_manager,
            self.window.tasks,
            target_format=duplicate_target_format(self.window.settings),
            extractor=extractor,
        )

    def _ask_duplicate_confirmation(self, total_count: int, duplicate_count: int) -> bool:
        """Ask whether duplicate playlist items should be excluded."""
        return ask_duplicate_confirmation_dialog(
            self.window,
            total_count,
            duplicate_count,
            STR.TITLE_DUPLICATE,
            STR.MSG_DUPLICATE_FOUND,
        )

    def _register_playlist_tasks(self, video_ids: list):
        """Register download tasks for playlist videos."""
        if self.task_list.closed:
            return
        self.window._show_task_list()
        self.window.status_label.setText(STR.MSG_REGISTERING_PLAYLIST.format(count=len(video_ids)))
        QApplication.processEvents()

        if self.task_list.closed:
            return
        with self.task_list.batch():
            for plan in build_playlist_task_plans(video_ids, STR.TPL_VIDEO_TITLE):
                self.window.total_tasks_in_queue += 1
                self.window._create_and_register_task(
                    self.window.total_tasks_in_queue,
                    plan.url,
                    plan.video_id,
                    extractor=plan.extractor,
                    title_override=plan.title_override,
                )

            self.window.status_label.setText(STR.MSG_ADDED_PLAYLIST.format(count=len(video_ids)))
            self.window.update_progress_ui()

    def on_playlist_analysis_finished(self, url, video_ids, success, error_msg, entry_count):
        """Handle completed playlist analysis."""
        if self.task_list.closed:
            return
        self._enable_url_input()

        if not success:
            self._handle_playlist_error(error_msg)
            return

        if not video_ids:
            message = (
                STR.MSG_PLAYLIST_EMPTY
                if entry_count == 0
                else STR.MSG_PLAYLIST_NO_AVAILABLE_VIDEOS
            )
            show_no_new_videos_dialog(
                self.window,
                STR.TITLE_NO_NEW_VIDEOS,
                message,
            )
            self.window.status_label.setText(STR.MSG_READY)
            return

        filtered_ids, duplicate_count = self._filter_duplicate_videos(video_ids)
        decision = build_playlist_registration_decision(
            video_ids,
            filtered_ids,
            duplicate_count,
            self._ask_duplicate_confirmation,
        )
        if self.task_list.closed:
            return

        if not decision.has_videos:
            show_no_new_videos_dialog(self.window, STR.TITLE_NO_NEW_VIDEOS, STR.MSG_NO_NEW_ITEMS)
            self.window.status_label.setText(STR.MSG_READY)
            return

        self._register_playlist_tasks(decision.video_ids)
