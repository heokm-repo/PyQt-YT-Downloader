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
from core.task_metadata import apply_metadata_to_task
from data.managers import TaskManager
from data.history_store import HistoryManager
from data.duplicate_checker import DuplicateChecker
from gui.tasks.task_list_controller import (
    TaskListController, sorted_task_ids,
    TASK_SORT_NEWEST, TASK_SORT_OLDEST, TASK_SORT_STATUS, TASK_STATUS_SORT_PRIORITY,
)
from gui.main_window.download_controller import DownloadController
from gui.tasks.thumbnail_loader import ThumbnailLoader
from gui.main_window.click_deselect import should_clear_selection_for_click
from core.scheduler_settings import target_worker_count
from core.download.workspace_cleanup import remove_workspace_cleanup_request
from core.task_summary import summarize_task_progress
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
    record_completed_media,
    media_completion_summary,
)
from gui.main_window.download_toggle import (
    build_download_toggle_plan,
    mark_downloading_tasks_paused,
    pause_downloading_tasks,
    resume_paused_tasks,
)
from gui.tasks.paused_task_cleanup import cleanup_cancelled_paused_tasks
from gui.tasks.task_actions import TaskActions
from gui.tasks.task_context_callbacks import build_task_context_callbacks
from gui.tasks.task_selection_plan import selected_tasks_for_ids
from gui.tasks.task_widget_signals import connect_task_widget_signals
from gui.main_window.view_state import show_task_list
from gui.main_window.language import MainWindowLanguageTexts, apply_main_window_language
from gui.main_window.theme import apply_main_window_theme
from gui.theme import apply_application_theme
from gui.dialogs.main_window_messages import confirm_resume_paused_tasks_dialog
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
from gui.main_window.shutdown import WindowShutdown
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
from constants import TaskStatus, APP_TITLE, DEFAULT_THEME, KEY_LANGUAGE, KEY_THEME, change_language
from data.models import DownloadTask
from core.scheduler import DownloadScheduler

from resources import colors, styles
from resources.styles import (
    MAIN_WINDOW_X, MAIN_WINDOW_Y, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT,
    MAIN_LAYOUT_MARGINS, MAIN_LAYOUT_SPACING,
    WINDOW_RESIZE_CONTENT_MARGIN,
    TITLE_BAR_HEIGHT,
)


class YTDownloaderPyQt5(WindowsCustomFrameMixin, QMainWindow):
    @property
    def tasks(self):
        return self.task_list.tasks

    @property
    def task_widgets(self):
        return self.task_list.widgets

    @property
    def selection_manager(self):
        return self.task_list.selection

    @property
    def visible_task_order(self):
        return self.task_list.visible_order

    @property
    def total_tasks_in_queue(self):
        return self.task_list.last_task_id

    @total_tasks_in_queue.setter
    def total_tasks_in_queue(self, value):
        self.task_list.last_task_id = value

    @property
    def playlist_worker(self):
        return self.download_controller.playlist_worker

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
        self.thumbnail_loader = ThumbnailLoader(self)
        self.task_list = TaskListController(self, self.thumbnail_loader)
        self.download_controller = DownloadController(self, self.task_list)
        self._settings_dialog = None
        self.settings = (
            dict(initial_settings) if initial_settings is not None else load_settings()
        )
        self.toggle_enabled = True
        self._restart_requested = False
        self._restart_launched = False
        self._close_saved = False

    def _init_interaction_services(self):
        """Create helpers that coordinate UI interactions."""
        self.context_menu_builder = ContextMenuBuilder(self)
        self.task_actions = TaskActions(self, self.task_list.batch)
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
        self._shutdown = WindowShutdown(self, self.scheduler, self.download_controller)
        self._shutdown.ready_to_close.connect(self.close)

    def _apply_initial_language(self):
        """Apply the saved language before UI text is created."""
        lang = self.settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        change_language(lang)

    def _restore_saved_window_state(self):
        """Restore saved geometry or center the window when restore fails."""
        state = load_window_state("MainWindow", settings=self.settings)
        restored = restore_window_state(
            "MainWindow", self, MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, state=state
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
        return self.tasks.get(task_id)

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
        return sorted_task_ids(self.tasks, self.task_widgets, self._current_task_sort_key())

    def _apply_task_sort_order(self):
        self.task_list.request_refresh(order=True)

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
        self.download_controller.pending_replacements.pop(task_id, None)
        self.task_list.remove(task_id, discard_workspace)

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
        return self.task_list.register(task_id, url, video_id, extractor, title_override)

    def _show_task_list(self):
        """Show the task-list UI."""
        show_task_list(self.scroll_area, self.empty_label)

    def _handle_playlist_download(self, clean_url: str):
        return self.download_controller._handle_playlist_download(clean_url)

    def _handle_single_video_download(self, clean_url: str, video_id: Optional[str], extractor: str = "unknown"):
        return self.download_controller._handle_single_video_download(clean_url, video_id, extractor)

    def _register_single_video_plan(self, plan):
        return self.download_controller._register_single_video_plan(plan)

    def _replace_active_duplicate(self, duplicate_task, plan):
        return self.download_controller._replace_active_duplicate(duplicate_task, plan)

    def start_download(self):
        return self.download_controller.start_download()

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
            summary = media_completion_summary(task)
            if summary:
                widget.status_label.setText(summary)
        else:
            if task:
                record_completed_media(task, self.history_manager)
            action = apply_failed_download_result(task, widget, message, STR.STATUS_PAUSED)
            if action == FailedDownloadAction.IGNORE_ALREADY_PAUSED:
                log.debug(f"Task {task_id}: already paused; skipping duplicate pause handling")
                return
            if action == FailedDownloadAction.IGNORE_RESUMING:
                log.info(f"Task {task_id}: ignored stale pause signal while resuming")
                return

        self.update_progress_ui()

    def update_progress_ui(self):
        self.task_list.request_refresh(order=self._current_task_sort_key() == TASK_SORT_STATUS, summary=True)

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
        return self.download_controller._enable_url_input()

    def _handle_playlist_error(self, error_msg: str):
        return self.download_controller._handle_playlist_error(error_msg)

    def _filter_duplicate_videos(self, video_ids: list, extractor: str = "youtube") -> tuple[list, int]:
        return self.download_controller._filter_duplicate_videos(video_ids, extractor)

    def _ask_duplicate_confirmation(self, total_count: int, duplicate_count: int) -> bool:
        return self.download_controller._ask_duplicate_confirmation(total_count, duplicate_count)

    def _register_playlist_tasks(self, video_ids: list):
        return self.download_controller._register_playlist_tasks(video_ids)

    @pyqtSlot(str, list, bool, str, int)
    def on_playlist_analysis_finished(self, url, video_ids, success, error_msg, entry_count):
        return self.download_controller.on_playlist_analysis_finished(url, video_ids, success, error_msg, entry_count)

    # --- Task Save/Load And Shutdown Handling ---

    def load_tasks_from_file(self):
        self.task_list.load_saved()

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
        if not self._shutdown.requested:
            self.task_list.close()
            self.download_controller.pending_replacements.clear()
            if self._settings_dialog is not None:
                self._settings_dialog.close()
                self._settings_dialog = None
            self.setEnabled(False)
            self._shutdown.begin()
        if not self._shutdown.ready:
            event.ignore()
            return

        if not self._close_saved:
            save_window_state("MainWindow", self)
            mark_downloading_tasks_paused(self.tasks)
            self.task_manager.save_tasks(self.tasks)
            self._close_saved = True

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
