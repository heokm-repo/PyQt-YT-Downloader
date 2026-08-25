from typing import Optional

from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QMainWindow,
    QShortcut,
)
from PyQt5.QtCore import Qt, pyqtSlot, QPoint, QEvent, QTimer
from PyQt5.QtGui import QKeySequence

from gui.windows.settings_dialog import SettingsDialog
from utils.settings_store import (
    consume_download_folder_fallback_notice,
    load_settings,
    save_settings,
)
from core.workers import PlaylistAnalysisWorker
from core.task_metadata import apply_metadata_to_task
from core.playlist_filter import filter_duplicate_videos
from core.url_processor import UrlProcessor
from data.managers import HistoryManager, TaskManager, DuplicateChecker
from gui.main_window.click_deselect import should_clear_selection_for_click
from gui.tasks.selection_manager import SelectionManager
from core.scheduler_settings import target_worker_count
from core.download.workspace_cleanup import remove_workspace_cleanup_request
from core.task_summary import summarize_task_progress
from gui.tasks.single_video_download import (
    build_single_video_download_plan,
    review_single_video_duplicate,
)
from gui.tasks.active_duplicate_replacement import wait_for_task_stop
from gui.main_window.smart_paste import extract_valid_clipboard_url
from gui.main_window.restart_policy import has_restart_sensitive_tasks
from gui.settings.settings_apply_plan import build_settings_apply_plan
from gui.dialogs.settings_fallback_notice import show_download_folder_fallback_notice
from gui.dialogs.messages import show_error
from gui.tasks.context_menu import ContextMenuBuilder
from gui.tasks.download_completion import (
    FailedDownloadAction,
    apply_failed_download_result,
    persist_download_output,
    record_successful_download,
)
from gui.tasks.duplicate_check_target import duplicate_target_format
from gui.main_window.download_toggle import (
    build_download_toggle_plan,
    mark_downloading_tasks_paused,
    pause_downloading_tasks,
    resume_paused_tasks,
)
from gui.tasks.paused_task_cleanup import cleanup_cancelled_paused_tasks
from gui.tasks.playlist_registration import build_playlist_registration_decision
from gui.tasks.playlist_task_plan import build_playlist_task_plans
from gui.tasks.task_actions import TaskActions
from gui.tasks.task_context_callbacks import build_task_context_callbacks
from gui.tasks.task_load_plan import (
    build_loaded_tasks,
    handle_paused_task_restore,
    loaded_tasks_need_workspace_persistence,
)
from gui.tasks.task_registration import register_download_task
from gui.tasks.task_selection_plan import selected_tasks_for_ids, tasks_except_id
from gui.tasks.task_status_message import build_task_status_message
from gui.tasks.task_workspace_cleanup import build_task_cleanup_request
from gui.tasks.task_widget_restore import create_restored_task_widget
from gui.tasks.task_widget_signals import connect_task_widget_signals
from gui.main_window.view_state import hide_task_list_if_empty, set_url_entry_enabled, show_task_list
from gui.main_window.language import MainWindowLanguageTexts, apply_main_window_language
from gui.main_window.theme import apply_main_window_theme
from gui.theme import apply_application_theme
from gui.dialogs.main_window_messages import (
    ask_duplicate_confirmation_dialog,
    ask_playlist_video_preference,
    confirm_duplicate_overwrite_dialog,
    confirm_resume_paused_tasks_dialog,
    show_invalid_url_dialog,
    show_no_new_videos_dialog,
    show_playlist_error_dialog,
)
from gui.main_window.controls import (
    create_main_content_layout,
    create_task_list_section as create_task_list_section_controls,
    create_status_bar as create_status_bar_controls,
    create_title_bar,
    create_url_input_section,
    set_button_icon,
)
from gui.main_window.chrome_state import (
    build_window_chrome_state,
    chrome_state_after_window_change,
    has_window_drag_started,
    should_continue_window_drag,
    should_start_window_drag,
    should_toggle_maximize_from_double_click,
)
from gui.main_window.worker_lifecycle import stop_running_worker
from gui.windowing.windows_custom_frame_mixin import WindowsCustomFrameMixin
from gui.windowing.window_state_manager import (
    load_window_state,
    save_window_state,
    restore_window_state,
)
from utils.logger import log
import constants  # Import the module too so dynamic language strings are always current.
from locales import DEFAULT_LANGUAGE
from locales.strings import STR
from constants import (
    TaskStatus,
    WORKER_TERMINATE_WAIT_MS, WORKER_SHUTDOWN_WAIT_MS,
    APP_TITLE,
    DEFAULT_THEME, KEY_LANGUAGE, KEY_THEME, change_language,
)
from data.models import DownloadTask
from core.scheduler import DownloadScheduler

TASK_SORT_NEWEST = "newest"
TASK_SORT_OLDEST = "oldest"
TASK_SORT_STATUS = "status"

TASK_STATUS_SORT_PRIORITY = {
    TaskStatus.FAILED: 0,
    TaskStatus.DOWNLOADING: 1,
    TaskStatus.PAUSED: 2,
    TaskStatus.WAITING: 3,
    TaskStatus.FINISHED: 4,
}

from resources import colors, styles
from resources.styles import (
    MAIN_WINDOW_X, MAIN_WINDOW_Y, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT,
    MAIN_LAYOUT_MARGINS, MAIN_LAYOUT_SPACING,
    WINDOW_RESIZE_CONTENT_MARGIN,
    TITLE_BAR_HEIGHT,
)


class YTDownloaderPyQt5(WindowsCustomFrameMixin, QMainWindow):
    def __init__(self, initial_settings=None):
        super().__init__()

        self._init_runtime_state(initial_settings)
        apply_application_theme(self.settings.get(KEY_THEME, DEFAULT_THEME))
        self._configure_window()
        self._init_interaction_services()
        self._init_data_services()
        self._create_download_scheduler()
        self._apply_initial_language()

        self.setup_ui()
        self.apply_language_to_ui()
        self._restore_saved_window_state()
        self._register_shortcuts()
        self.load_tasks_from_file()
        self._initialize_scheduler()
        QTimer.singleShot(0, self._show_pending_settings_fallback_notice)

    def _configure_window(self):
        """Apply fixed main-window flags, geometry, and base styling."""
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(MAIN_WINDOW_X, MAIN_WINDOW_Y, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT)
        self.setStyleSheet(styles.MAIN_WINDOW_STYLE)

    def _init_runtime_state(self, initial_settings=None):
        """Initialize mutable state owned directly by the main window."""
        self._is_maximized_state = False
        self.oldPos = None
        self._window_drag_active = False
        self.tasks: list[DownloadTask] = []
        self.task_widgets = {}
        self.visible_task_order: list[int] = []
        self.total_tasks_in_queue = 0
        self.playlist_worker = None
        self._settings_dialog = None
        self.settings = (
            dict(initial_settings) if initial_settings is not None else load_settings()
        )
        self.toggle_enabled = True
        self._restart_requested = False
        self._restart_launched = False
        self._pending_duplicate_replacements = {}

    def _init_interaction_services(self):
        """Create helpers that coordinate UI interactions."""
        self.selection_manager = SelectionManager()
        self.context_menu_builder = ContextMenuBuilder(self)
        self.task_actions = TaskActions(self)
        self._click_deselect_targets = []

    def _init_data_services(self):
        """Create persistence and duplicate-checking services."""
        self.history_manager = HistoryManager()
        self.task_manager = TaskManager()
        self.duplicate_checker = DuplicateChecker(self.history_manager)

    def _create_download_scheduler(self):
        """Create the scheduler and connect its signals to this window."""
        self.scheduler = DownloadScheduler(self)
        self.scheduler.progress_updated.connect(self.on_progress_updated)
        self.scheduler.download_finished.connect(self.on_download_finished)
        self.scheduler.task_started.connect(self.on_task_started)
        self.scheduler.metadata_fetched.connect(self.on_metadata_fetched)

    def _apply_initial_language(self):
        """Apply the saved language before UI text is created."""
        lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        change_language(lang)

    def _restore_saved_window_state(self):
        """Restore saved geometry or center the window when restore fails."""
        state = load_window_state("MainWindow")
        restored = restore_window_state(
            "MainWindow", self, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT
        )
        if not restored:
            self.center_window()
        elif state and state.get("maximized", False):
            self._apply_window_chrome_state(True)

    def _register_shortcuts(self):
        """Register global shortcuts handled by the main window."""
        self.paste_shortcut = QShortcut(QKeySequence.Paste, self)
        self.paste_shortcut.activated.connect(self.handle_smart_paste)

        self.select_all_shortcut = QShortcut(QKeySequence.SelectAll, self)
        self.select_all_shortcut.activated.connect(self.select_all_tasks)

    # --- Helper Methods ---
    
    def _show_pending_settings_fallback_notice(self):
        """Show the settings fallback notice produced while loading or saving settings."""
        notice = consume_download_folder_fallback_notice()
        if notice is None:
            return

        show_download_folder_fallback_notice(
            self,
            notice,
            STR.TITLE_WARNING,
            STR.MSG_DOWNLOAD_FOLDER_FALLBACK,
        )

    def get_task_by_id(self, task_id: int) -> Optional[DownloadTask]:
        """Find a DownloadTask by task_id."""
        return next((t for t in self.tasks if t.id == task_id), None)

    # --- UI Creation Methods ---

    def setup_ui(self):
        self.menuBar().hide()

        controls = create_main_content_layout(
            styles.CENTRAL_WIDGET_STYLE,
            MAIN_LAYOUT_MARGINS,
            MAIN_LAYOUT_SPACING,
        )
        self.setCentralWidget(controls.central_widget)
        self._main_layout = controls.main_layout

        self.create_custom_title_bar(self._main_layout)
        self.create_url_section(self._main_layout)
        self.create_task_list_section(self._main_layout)
        self.create_status_bar(self._main_layout)
        self._init_windows_custom_frame(
            enabled=True,
            content_margin=WINDOW_RESIZE_CONTENT_MARGIN,
        )

    def _apply_window_chrome_state(self, is_maximized: bool):
        """Apply the central-widget style and title-bar icon."""
        chrome_state = build_window_chrome_state(
            is_maximized,
            styles.CENTRAL_WIDGET_STYLE,
            styles.CENTRAL_WIDGET_MAXIMIZED_STYLE,
        )
        self._is_maximized_state = chrome_state.is_maximized

        central = self.centralWidget()
        if central:
            central.setStyleSheet(chrome_state.central_style)
        if hasattr(self, 'maximize_btn'):
            set_button_icon(
                self.maximize_btn,
                chrome_state.maximize_icon_name,
                hover_color=colors.COLOR_TITLE_BAR_HOVER_ICON,
            )

    def apply_language_to_ui(self):
        """Apply current localized strings to existing UI controls."""
        apply_main_window_language(
            self,
            MainWindowLanguageTexts(
                title=constants.APP_TITLE,
                url_placeholder=STR.MAIN_URL_PLACEHOLDER,
                download_text=STR.BTN_DOWNLOAD,
                empty_text=STR.MAIN_EMPTY_STATE,
                ready_text=STR.MAIN_STATUS_READY,
            ),
            has_tasks=bool(self.tasks),
        )
        self._refresh_task_sort_button_labels()
        self._update_task_counter_ui()

    def _task_sort_options(self):
        """Return localized sort options for the task-list selector."""
        return (
            (TASK_SORT_NEWEST, STR.SORT_NEWEST),
            (TASK_SORT_OLDEST, STR.SORT_OLDEST),
            (TASK_SORT_STATUS, STR.SORT_STATUS),
        )

    def _refresh_task_sort_button_labels(self):
        """Refresh sort button text while preserving the selected sort key."""
        if not hasattr(self, "task_sort_button"):
            return

        was_blocked = self.task_sort_button.blockSignals(True)
        self.task_sort_button.setSortOptions(self._task_sort_options())
        self.task_sort_button.blockSignals(was_blocked)

    def _current_task_sort_key(self) -> str:
        if not hasattr(self, "task_sort_button"):
            return TASK_SORT_NEWEST
        return self.task_sort_button.currentKey() or TASK_SORT_NEWEST

    def _sorted_task_ids(self) -> list[int]:
        sort_key = self._current_task_sort_key()
        if sort_key == TASK_SORT_OLDEST:
            ordered_tasks = sorted(self.tasks, key=lambda task: task.id)
        elif sort_key == TASK_SORT_STATUS:
            ordered_tasks = sorted(
                self.tasks,
                key=lambda task: (
                    TASK_STATUS_SORT_PRIORITY.get(task.status, len(TASK_STATUS_SORT_PRIORITY)),
                    -task.id,
                ),
            )
        else:
            ordered_tasks = sorted(self.tasks, key=lambda task: task.id, reverse=True)
        return [task.id for task in ordered_tasks if task.id in self.task_widgets]

    def _apply_task_sort_order(self):
        """Reorder visible task widgets without mutating the source task list."""
        if not hasattr(self, "task_layout"):
            return

        ordered_task_ids = self._sorted_task_ids()
        self.visible_task_order = ordered_task_ids
        ordered_widgets = [self.task_widgets[task_id] for task_id in ordered_task_ids]
        for widget in ordered_widgets:
            self.task_layout.removeWidget(widget)

        insert_index = max(0, self.task_layout.count() - 1)
        for widget in ordered_widgets:
            self.task_layout.insertWidget(insert_index, widget)
            insert_index += 1

    def _handle_task_sort_changed(self, _sort_key: str):
        self._apply_task_sort_order()

    def _update_task_counter_ui(self, summary=None):
        """Update the finished/total counter and existing completion progress bar."""
        if summary is None:
            summary = summarize_task_progress(self.tasks)

        if hasattr(self, "task_counter_label"):
            self.task_counter_label.setText(f"{summary.finished}/{summary.total}")

        if hasattr(self, "progress_slider"):
            if summary.total == 0:
                progress_value = self.progress_slider.minimum()
            else:
                progress_value = round(summary.finished * self.progress_slider.maximum() / summary.total)
            self.progress_slider.setValue(progress_value)

    def create_custom_title_bar(self, layout):
        controls = create_title_bar(
            APP_TITLE,
            styles.TITLE_BAR_STYLE,
            styles.MINIMIZE_BUTTON_STYLE,
            styles.MAXIMIZE_BUTTON_STYLE,
            styles.CLOSE_BUTTON_STYLE,
            self.showMinimized,
            self._toggle_maximize,
            self.close,
        )
        self.title_bar_frame = controls.frame
        self.app_title_label = controls.title_label
        self.minimize_btn = controls.minimize_button
        self.maximize_btn = controls.maximize_button
        self.close_btn = controls.close_button
        layout.addWidget(controls.frame)

    # --- Window maximize toggle ---
    
    def _toggle_maximize(self):
        """Toggle between maximized and restored states."""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    # -- Mouse Events: Resize and Drag -------------------------------------

    def _is_title_bar_drag_position(self, global_pos):
        """Return True when the global cursor position is inside the title bar."""
        if not hasattr(self, "title_bar_frame"):
            return False
        return self.title_bar_frame.rect().contains(
            self.title_bar_frame.mapFromGlobal(global_pos)
        )
    
    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            if should_start_window_drag(
                event.button(),
                Qt.LeftButton,
                self._is_title_bar_drag_position(event.globalPos()),
            ):
                self.oldPos = event.globalPos()
                self._window_drag_active = False
    
    def mouseMoveEvent(self, event):
        if should_continue_window_drag(self.oldPos, event.buttons(), Qt.LeftButton):
            global_pos = event.globalPos()
            if not self._window_drag_active:
                if not has_window_drag_started(
                    self.oldPos,
                    global_pos,
                    QApplication.startDragDistance(),
                ):
                    return
                self._window_drag_active = True

            # Restore before dragging while maximized.
            if self._is_maximized_state:
                self.showNormal()
                self.oldPos = global_pos
                return
            delta = QPoint(global_pos - self.oldPos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.oldPos = global_pos
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = None
            self._window_drag_active = False
    
    def mouseDoubleClickEvent(self, event):
        """Toggle maximize when the title bar is double-clicked."""
        if should_toggle_maximize_from_double_click(
            event.button(),
            Qt.LeftButton,
            event.pos().y(),
            TITLE_BAR_HEIGHT,
        ):
            self._toggle_maximize()
            return
        super().mouseDoubleClickEvent(event)
    
    def changeEvent(self, event):
        """Sync custom chrome when the OS changes the window state."""
        if event.type() == QEvent.WindowStateChange:
            chrome_state = chrome_state_after_window_change(
                self.isMaximized(),
                self.isMinimized(),
                self._is_maximized_state,
            )
            if chrome_state is not None:
                self._apply_window_chrome_state(chrome_state)
                if chrome_state:
                    log.info("Window maximized (MainWindow)")
                else:
                    log.info("Window restored (MainWindow)")
        super().changeEvent(event)
    
    def eventFilter(self, source, event):
        """Clear selection when registered background areas are clicked."""
        if (
            event.type() == QEvent.MouseButtonPress
            and event.button() == Qt.LeftButton
            and should_clear_selection_for_click(
                source,
                event.pos(),
                self._click_deselect_targets,
                self.task_widgets.values(),
            )
        ):
            self.selection_manager.clear(self.task_widgets)
            self.setFocus()
        return super().eventFilter(source, event)

    def create_url_section(self, layout):
        controls = create_url_input_section(
            STR.MAIN_URL_PLACEHOLDER,
            STR.BTN_DOWNLOAD,
            self.toggle_download,
            self.start_download,
            self.open_download_options,
        )
        self.toggle_btn = controls.toggle_button
        self.url_section_frame = controls.frame
        self.url_input = controls.url_input
        self.download_btn = controls.download_button
        self.settings_btn = controls.settings_button
        layout.addWidget(controls.frame)

    def create_task_list_section(self, layout):
        controls = create_task_list_section_controls(STR.ERR_START_FAIL)
        controls.scroll_content.installEventFilter(self)
        self._click_deselect_targets.append(controls.scroll_content)
        self.scroll_area = controls.scroll_area
        self.scroll_content = controls.scroll_content
        self.task_layout = controls.task_layout
        self.empty_label = controls.empty_label
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.empty_label)

    def create_status_bar(self, layout):
        controls = create_status_bar_controls(
            STR.MAIN_STATUS_READY,
            self._task_sort_options(),
            "0/0",
        )
        controls.frame.installEventFilter(self)
        self._click_deselect_targets.append(controls.frame)
        self.task_sort_button = controls.sort_button
        self.status_bar_frame = controls.frame
        self.status_label = controls.status_label
        self.progress_slider = controls.progress_slider
        self.task_counter_label = controls.counter_label
        self.task_sort_button.sortChanged.connect(self._handle_task_sort_changed)
        layout.addWidget(controls.frame)

    # --- Keyboard Shortcut Handlers ---
    
    def handle_smart_paste(self):
        """Paste into the URL input or start a download from a valid clipboard URL."""
        focused_widget = QApplication.focusWidget()
        if focused_widget == self.url_input:
            self.url_input.paste()
            return

        url = extract_valid_clipboard_url(QApplication.clipboard().text())
        if url:
            self.url_input.setText(url)
            self.start_download()
            self.status_label.setText(STR.MSG_SMART_PASTE)

    # --- Task Control Methods Delegated To TaskActions ---

    def pause_task(self, task_id):
        """Pause one task."""
        self.task_actions.pause_task(task_id)

    def resume_task(self, task_id):
        """Resume a paused task."""
        self.task_actions.resume_task(task_id)

    def retry_task(self, task_id):
        """Retry a download."""
        self.task_actions.retry_task(task_id)

    # --- File Action Methods Delegated To TaskActions ---

    def play_file(self, task_id):
        """Play a file."""
        self.task_actions.play_file(task_id)

    def open_folder(self, task_id):
        """Open the folder containing a file."""
        self.task_actions.open_folder(task_id)

    def delete_file(self, task_id, confirm=True):
        """Delete a file and remove it from the list."""
        self.task_actions.delete_file(task_id, confirm)

    # --- Signal Connections ---
    
    def _connect_task_widget_signals(self, task_widget):
        """Connect TaskWidget signals to main-window handlers."""
        connect_task_widget_signals(task_widget, self)

    # --- Selection Management Methods ---
    
    def on_task_clicked(self, task_id, modifiers):
        """Handle card clicks for single, Shift, and Ctrl selection."""
        self.selection_manager.handle_click(
            task_id, modifiers, self.task_widgets, self.task_layout
        )
    
    def select_all_tasks(self):
        """Select all tasks with Ctrl+A."""
        # Let the URL input keep its default behavior when focused.
        focused_widget = QApplication.focusWidget()
        if focused_widget == self.url_input:
            self.url_input.selectAll()
            return
        
        # Select all cards.
        self.selection_manager.select_all(self.task_widgets)
    
    def show_context_menu(self, task_id, global_pos):
        """Show the task context menu."""
        if not self.selection_manager.is_selected(task_id):
            self.selection_manager.handle_click(task_id, 0, self.task_widgets, self.task_layout)

        selected_ids = self.selection_manager.get_selected_ids()
        selected_tasks = selected_tasks_for_ids(selected_ids, self.tasks)
        callbacks = build_task_context_callbacks(self, selected_ids)

        menu = self.context_menu_builder.build(selected_tasks, callbacks)
        menu.exec_(global_pos)

    def _pause_selected_tasks(self):
        """Pause selected tasks."""
        self.task_actions.pause_selected(self.selection_manager.get_selected_ids())
    
    def _resume_selected_tasks(self):
        """Resume selected tasks."""
        self.task_actions.resume_selected(self.selection_manager.get_selected_ids())
    
    def _retry_selected_tasks(self):
        """Retry selected tasks."""
        task_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.retry_selected(task_ids)
    
    def _open_folders_for_selected(self):
        """Open folders for selected tasks."""
        self.task_actions.open_folders_for_selected(self.selection_manager.get_selected_ids())
    
    def _delete_files_for_selected(self):
        """Delete files for selected tasks."""
        selected_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.delete_files_for_selected(selected_ids, self.tasks)
    
    def _remove_selected_from_list(self):
        """Remove selected tasks from the list."""
        task_ids = self.selection_manager.get_selected_ids()
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.remove_selected_from_list(task_ids)

    def _remove_all_completed_from_list(self):
        """Remove all completed tasks from the list."""
        self.selection_manager.clear(self.task_widgets)
        self.task_actions.remove_all_completed_from_list()

    def _discard_removed_task_workspace(
        self,
        cleanup_request,
        attempts_left=12,
    ):
        removed = remove_workspace_cleanup_request(cleanup_request)
        if not removed and attempts_left > 0:
            QTimer.singleShot(
                250,
                lambda: self._discard_removed_task_workspace(
                    cleanup_request,
                    attempts_left - 1,
                ),
            )

    def remove_task_from_list(self, task_id, discard_workspace=True):
        """Remove a task card from the list without deleting its file."""
        task = self.get_task_by_id(task_id)
        widget = self.task_widgets.get(task_id)
        if not widget:
            return

        self._pending_duplicate_replacements.pop(task_id, None)
        if discard_workspace and task:
            cleanup_request = build_task_cleanup_request(task)
            if task.status in (
                TaskStatus.WAITING,
                TaskStatus.DOWNLOADING,
                TaskStatus.PAUSED,
            ):
                self.scheduler.cancel_task(task_id)
            self._discard_removed_task_workspace(cleanup_request)
        
        self.selection_manager.remove_from_selection(task_id)

        self.task_layout.removeWidget(widget)
        widget.deleteLater()
        
        del self.task_widgets[task_id]
        self.tasks = tasks_except_id(self.tasks, task_id)
        hide_task_list_if_empty(self.task_widgets, self.scroll_area, self.empty_label)
        self.update_progress_ui()

    # --- Global download toggle ---

    def update_toggle_button_style(self):
        self.toggle_btn.setPlaying(self.toggle_enabled)

    def toggle_download(self):
        plan = build_download_toggle_plan(
            self.toggle_enabled,
            STR.MSG_DL_ENABLED,
            STR.MSG_DL_PAUSED,
        )
        self.toggle_enabled = plan.enabled
        self.update_toggle_button_style()
        self.status_label.setText(plan.status_text)

        if plan.enabled:
            resume_paused_tasks(
                self.tasks,
                self.task_widgets,
                self.scheduler,
                self.settings,
                STR.STATUS_WAITING_DOTS,
            )
            self.scheduler.resume_all()
        else:
            pause_downloading_tasks(self.tasks, self.task_widgets)
            self.scheduler.pause_all()

        self.update_progress_ui()
        
    def center_window(self):
        screen = self.screen().geometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)

    # --- Download Start And Task Registration ---

    def _create_and_register_task(
        self,
        task_id: int,
        url: str,
        video_id: Optional[str] = None,
        extractor: str = "unknown",
        title_override: Optional[str] = None,
    ) -> DownloadTask:
        """Create a task widget, register the task, and enqueue it."""
        task = register_download_task(
            task_id,
            url,
            self.settings,
            self,
            self.task_layout,
            self.task_widgets,
            self._connect_task_widget_signals,
            self.tasks,
            self.scheduler,
            video_id,
            extractor,
            title_override,
        )
        self._apply_task_sort_order()
        return task

    def _show_task_list(self):
        """Show the task-list UI."""
        show_task_list(self.scroll_area, self.empty_label)

    def _handle_playlist_download(self, clean_url: str):
        """Start playlist analysis after stopping any previous analysis worker."""
        worker_stop = stop_running_worker(self.playlist_worker, WORKER_TERMINATE_WAIT_MS)
        if worker_stop.timed_out:
            log.warning("Previous playlist worker did not stop before timeout.")

        self.status_label.setText(STR.MSG_ANALYZING_PLAYLIST)
        set_url_entry_enabled(self.url_input, self.download_btn, False)

        self.playlist_worker = PlaylistAnalysisWorker(clean_url, self)
        self.playlist_worker.analysis_finished.connect(self.on_playlist_analysis_finished)
        self.playlist_worker.start()

    def _handle_single_video_download(self, clean_url: str, video_id: Optional[str], extractor: str = "unknown"):
        """Handle registration for a single video download."""
        plan = build_single_video_download_plan(
            clean_url,
            video_id,
            extractor,
            self.settings,
        )

        duplicate_decision = review_single_video_duplicate(
            self.duplicate_checker,
            plan.duplicate_target,
            self.tasks[:],
            lambda message: confirm_duplicate_overwrite_dialog(
                self,
                STR.MSG_DUPLICATE_CHECK,
                message,
            ),
        )
        if duplicate_decision.cancelled:
            self.status_label.setText(STR.MSG_DL_CANCELLED)
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
        self.total_tasks_in_queue += 1
        task_id = self.total_tasks_in_queue
        self._create_and_register_task(
            task_id,
            plan.clean_url,
            plan.video_id,
            plan.extractor,
        )

        self.status_label.setText(STR.MSG_ADDED_QUEUE)
        self.update_progress_ui()

    def _replace_active_duplicate(self, duplicate_task, plan):
        """Cancel an active duplicate and replace it only after it stops."""
        task_id = duplicate_task.id
        if task_id in self._pending_duplicate_replacements:
            self.status_label.setText(STR.MSG_DL_CANCELLED)
            return

        pending = (duplicate_task, plan)
        self._pending_duplicate_replacements[task_id] = pending
        self.scheduler.cancel_task(task_id)

        def finalize_replacement():
            if self._pending_duplicate_replacements.get(task_id) != pending:
                return
            self._pending_duplicate_replacements.pop(task_id, None)
            if self.get_task_by_id(task_id) is not duplicate_task:
                return
            self.remove_task_from_list(task_id)
            self._register_single_video_plan(plan)

        def replacement_timeout():
            if self._pending_duplicate_replacements.get(task_id) != pending:
                return
            self._pending_duplicate_replacements.pop(task_id, None)
            self.status_label.setText(STR.MSG_DL_CANCELLED)
            show_error(
                self,
                STR.TITLE_ERROR,
                STR.ERR_DUPLICATE_REPLACEMENT_TIMEOUT,
            )

        QTimer.singleShot(
            0,
            lambda: wait_for_task_stop(
                self.scheduler,
                task_id,
                QTimer.singleShot,
                finalize_replacement,
                replacement_timeout,
            ),
        )

    def start_download(self):
        """Orchestrate download start."""
        url = self.url_input.text().strip()
        prefer_playlist = False

        if UrlProcessor.requires_playlist_preference(url):
            preference = ask_playlist_video_preference(
                self,
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
        result = UrlProcessor.process_url(url, prefer_playlist=prefer_playlist)
        if not result:
            show_invalid_url_dialog(self, STR.TITLE_ERROR, STR.ERR_INVALID_URL)
            return

        self.url_input.clear()
        self._show_task_list()

        # Branch between playlist and single-video handling.
        if result.is_playlist:
            self._handle_playlist_download(result.clean_url)
        else:
            self._handle_single_video_download(result.clean_url, result.video_id, result.extractor or 'unknown')

    # --- Scheduler Signal Handlers ---
        
    @pyqtSlot(int)
    def on_task_started(self, task_id):
        widget = self.task_widgets.get(task_id)
        if widget:
            widget.set_started()
            
            # Update task state.
            task = self.get_task_by_id(task_id)
            if task: task.status = TaskStatus.DOWNLOADING
        
        self.update_progress_ui()

    @pyqtSlot(dict, int)
    def on_progress_updated(self, progress_dict, task_id):
        widget = self.task_widgets.get(task_id)
        if widget:
            widget.update_progress(progress_dict)

    @pyqtSlot(bool, str, int, str)
    def on_download_finished(self, success, message, task_id, final_path):
        widget = self.task_widgets.get(task_id)
        if not widget:
            return

        task = self.get_task_by_id(task_id)
        persist_download_output(task, final_path, success)

        if success:
            file_size = record_successful_download(task, self.history_manager)
            widget.set_finished(file_size=file_size)
        else:
            action = apply_failed_download_result(task, widget, message, STR.STATUS_PAUSED)
            if action == FailedDownloadAction.IGNORE_ALREADY_PAUSED:
                log.debug(f"Task {task_id}: already paused; skipping duplicate pause handling")
                return
            if action == FailedDownloadAction.IGNORE_RESUMING:
                log.info(f"Task {task_id}: ignored stale pause signal while resuming")
                return

        self.update_progress_ui()

    def update_progress_ui(self):
        """Update the status bar from current task progress."""
        summary = summarize_task_progress(self.tasks)
        self.status_label.setText(
            build_task_status_message(
                self.tasks,
                STR.MSG_READY,
                STR.MSG_ERROR_COUNT,
                STR.MSG_COMPLETED_COUNT,
            )
        )
        self._update_task_counter_ui(summary)
        if self._current_task_sort_key() == TASK_SORT_STATUS:
            self._apply_task_sort_order()

    # --- Settings management ---

    def open_download_options(self):
        """Open the non-modal settings dialog without blocking the main window."""
        if self._settings_dialog is not None:
            self._settings_dialog.show()
            self._settings_dialog.raise_()
            self._settings_dialog.activateWindow()
            return

        dialog = SettingsDialog(
            self.settings.copy(),
            parent=self,
            active_task_check=lambda: has_restart_sensitive_tasks(self.tasks),
        )
        dialog.setWindowModality(Qt.NonModal)
        self._settings_dialog = dialog
        dialog.finished.connect(self._handle_settings_dialog_finished)
        dialog.show()

    def _handle_settings_dialog_finished(self, result):
        """Apply the result from the non-modal settings dialog."""
        dialog = self._settings_dialog
        self._settings_dialog = None
        if dialog is None:
            return

        try:
            if dialog.restart_requested:
                self._request_restart()
                return
            if result != QDialog.Accepted:
                return

            new_settings = dialog.get_new_settings()
            apply_plan = build_settings_apply_plan(self.settings, new_settings)
            self.settings = new_settings
            save_settings(self.settings)

            if apply_plan.theme_changed:
                apply_application_theme(apply_plan.theme)
                apply_main_window_theme(self)

            change_language(apply_plan.language)
            self.apply_language_to_ui()

            if apply_plan.adjust_worker_count:
                self.scheduler.adjust_worker_count(apply_plan.worker_count)

            self._show_pending_settings_fallback_notice()
        finally:
            dialog.deleteLater()

    def _request_restart(self):
        """Close through the normal shutdown path and relaunch the app."""
        if self._restart_requested:
            return
        self._restart_requested = True
        self.close()

    def _initialize_scheduler(self):
        """Initialize scheduler workers from current settings."""
        self.scheduler.initialize(target_worker_count(self.settings))
    
    @pyqtSlot(int, dict)
    def on_metadata_fetched(self, task_id, metadata):
        """Update UI and task metadata fetched by the worker."""
        widget = self.task_widgets.get(task_id)
        if not widget:
            return

        widget.update_metadata(metadata)

        task = self.get_task_by_id(task_id)
        if task:
            apply_metadata_to_task(task, metadata)

    # --- Playlist Handling ---
    
    def _enable_url_input(self):
        """Enable URL entry controls after playlist analysis."""
        set_url_entry_enabled(self.url_input, self.download_btn, True)

    def _handle_playlist_error(self, error_msg: str):
        """Show playlist errors and return the status bar to ready."""
        show_playlist_error_dialog(
            self,
            STR.TITLE_ERROR,
            error_msg,
            STR.ERR_PLAYLIST_FETCH,
        )
        self.status_label.setText(STR.MSG_READY)

    def _filter_duplicate_videos(self, video_ids: list, extractor: str = "youtube") -> tuple[list, int]:
        """Filter already downloaded or queued playlist videos."""
        return filter_duplicate_videos(
            video_ids,
            self.history_manager,
            self.tasks,
            target_format=duplicate_target_format(self.settings),
            extractor=extractor,
        )

    def _ask_duplicate_confirmation(self, total_count: int, duplicate_count: int) -> bool:
        """Ask whether duplicate playlist items should be excluded."""
        return ask_duplicate_confirmation_dialog(
            self,
            total_count,
            duplicate_count,
            STR.TITLE_DUPLICATE,
            STR.MSG_DUPLICATE_FOUND,
        )

    def _register_playlist_tasks(self, video_ids: list):
        """Register download tasks for playlist videos."""
        self._show_task_list()
        self.status_label.setText(STR.MSG_REGISTERING_PLAYLIST.format(count=len(video_ids)))
        QApplication.processEvents()

        for plan in build_playlist_task_plans(video_ids, STR.TPL_VIDEO_TITLE):
            self.total_tasks_in_queue += 1
            self._create_and_register_task(
                self.total_tasks_in_queue,
                plan.url,
                plan.video_id,
                extractor=plan.extractor,
                title_override=plan.title_override,
            )

        self.status_label.setText(STR.MSG_ADDED_PLAYLIST.format(count=len(video_ids)))
        self.update_progress_ui()

    @pyqtSlot(str, list, bool, str, int)
    def on_playlist_analysis_finished(self, url, video_ids, success, error_msg, entry_count):
        """Handle completed playlist analysis."""
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
                self,
                STR.TITLE_NO_NEW_VIDEOS,
                message,
            )
            self.status_label.setText(STR.MSG_READY)
            return

        filtered_ids, duplicate_count = self._filter_duplicate_videos(video_ids)
        decision = build_playlist_registration_decision(
            video_ids,
            filtered_ids,
            duplicate_count,
            self._ask_duplicate_confirmation,
        )

        if not decision.has_videos:
            show_no_new_videos_dialog(self, STR.TITLE_NO_NEW_VIDEOS, STR.MSG_NO_NEW_ITEMS)
            self.status_label.setText(STR.MSG_READY)
            return

        self._register_playlist_tasks(decision.video_ids)

    # --- Task Save/Load And Shutdown Handling ---

    def load_tasks_from_file(self):
        """Load saved tasks and restore their widgets."""
        loaded_tasks = self.task_manager.load_tasks()
        if not loaded_tasks:
            return

        show_task_list(self.scroll_area, self.empty_label)

        loaded_task_objects, max_id = build_loaded_tasks(loaded_tasks)
        for task in loaded_task_objects:
            create_restored_task_widget(
                task,
                self,
                self.task_layout,
                self.task_widgets,
                self._connect_task_widget_signals,
            )
            self.tasks.append(task)

        if loaded_tasks_need_workspace_persistence(loaded_tasks):
            # Persist assigned UUIDs before any resume migration starts.
            self.task_manager.save_tasks(self.tasks)

        self._apply_task_sort_order()

        if max_id > self.total_tasks_in_queue:
            self.total_tasks_in_queue = max_id
        self.update_progress_ui()

        handle_paused_task_restore(
            self.tasks,
            self._confirm_resume_paused_tasks,
            self.resume_task,
            self._cleanup_temp_files,
        )

    def _confirm_resume_paused_tasks(self):
        """Ask whether paused loaded tasks should be resumed."""
        return confirm_resume_paused_tasks_dialog(
            self,
            STR.TITLE_RESUME,
            STR.MSG_RESUME_CONFIRM,
        )

    def _cleanup_temp_files(self, tasks):
        """Delete paused task temp files and mark them retryable."""
        cleanup_cancelled_paused_tasks(tasks, self.task_widgets)

    def closeEvent(self, event):
        if self._settings_dialog is not None:
            self._settings_dialog.close()
            self._settings_dialog = None

        save_window_state("MainWindow", self)
        mark_downloading_tasks_paused(self.tasks)
        self.task_manager.save_tasks(self.tasks)

        worker_stop = stop_running_worker(self.playlist_worker, WORKER_SHUTDOWN_WAIT_MS)
        if worker_stop.timed_out:
            log.warning("Playlist worker did not stop before timeout.")

        self.scheduler.shutdown()

        if self._restart_requested and not self._restart_launched:
            from utils.app_restart import launch_restart

            self._restart_launched = launch_restart()
            if self._restart_launched:
                log.info("Replacement application process started.")
            else:
                log.error("Failed to start replacement application process.")
                show_error(
                    self,
                    STR.TITLE_ERROR,
                    STR.ERR_RESTART_FAILED,
                )
        event.accept()
