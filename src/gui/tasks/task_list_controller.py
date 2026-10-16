"""Own task membership and reconcile list presentation once per command."""
from contextlib import contextmanager

from constants import TaskStatus
from core.task_summary import summarize_task_progress
from data.task_collection import TaskCollection
from gui.main_window.view_state import hide_task_list_if_empty, show_task_list
from gui.tasks.selection_manager import SelectionManager
from gui.tasks.task_load_plan import (
    build_loaded_tasks, handle_paused_task_restore, loaded_tasks_need_workspace_persistence,
)
from gui.tasks.task_registration import register_download_task
from gui.tasks.task_status_message import build_task_status_message
from gui.tasks.task_widget_restore import create_restored_task_widget
from gui.tasks.task_workspace_cleanup import build_task_cleanup_request
from locales.strings import STR


TASK_SORT_NEWEST = 'newest'
TASK_SORT_OLDEST = 'oldest'
TASK_SORT_STATUS = 'status'
TASK_STATUS_SORT_PRIORITY = {
    TaskStatus.FAILED: 0, TaskStatus.DOWNLOADING: 1, TaskStatus.PAUSED: 2,
    TaskStatus.WAITING: 3, TaskStatus.FINISHED: 4,
}


def sorted_task_ids(tasks, widgets, sort_key):
    if sort_key == TASK_SORT_OLDEST:
        ordered = sorted(tasks, key=lambda task: task.id)
    elif sort_key == TASK_SORT_STATUS:
        ordered = sorted(tasks, key=lambda task: (
            TASK_STATUS_SORT_PRIORITY.get(task.status, len(TASK_STATUS_SORT_PRIORITY)), -task.id))
    else:
        ordered = sorted(tasks, key=lambda task: task.id, reverse=True)
    return [task.id for task in ordered if task.id in widgets]


class TaskListController:
    def __init__(self, view, thumbnail_loader=None):
        self.view = view
        self.thumbnail_loader = thumbnail_loader
        self.tasks = TaskCollection()
        self.widgets = {}
        self.selection = SelectionManager()
        self.visible_order = []
        self.last_task_id = 0
        self.closed = False
        self._batch_depth = 0
        self._order_dirty = False
        self._summary_dirty = False

    @contextmanager
    def batch(self):
        """Nestable UI transaction; keep partial successful changes on failure."""
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if not self._batch_depth:
                self.flush()

    def request_refresh(self, *, order=False, summary=False):
        if self.closed:
            return
        self._order_dirty |= order
        self._summary_dirty |= summary
        if not self._batch_depth:
            self.flush()

    def flush(self):
        if self.closed:
            return
        order, summary = self._order_dirty, self._summary_dirty
        self._order_dirty = self._summary_dirty = False
        if order:
            self._reconcile_order()
        if summary:
            progress = summarize_task_progress(self.tasks)
            self.view.status_label.setText(build_task_status_message(
                self.tasks, STR.MSG_READY, STR.MSG_ERROR_COUNT, STR.MSG_COMPLETED_COUNT,
                summary=progress))
            self.view._update_task_counter_ui(progress)
            hide_task_list_if_empty(self.widgets, self.view.scroll_area, self.view.empty_label)

    def _reconcile_order(self):
        view = self.view
        if not hasattr(view, 'task_layout'):
            return
        ordered = view._sorted_task_ids()
        layout = view.task_layout
        # Inspect the actual layout: new widgets may not be inserted yet and
        # removals can already leave the remaining widgets in the right order.
        for index, task_id in enumerate(ordered):
            widget = self.widgets[task_id]
            item = layout.itemAt(index)
            if item is None or item.widget() is not widget:
                layout.insertWidget(index, widget)
        self.visible_order = ordered

    def register(self, task_id, url, video_id=None, extractor='unknown', title_override=None):
        if self.closed:
            return None
        view = self.view
        with self.batch():
            try:
                return register_download_task(
                    task_id, url, view.settings, view, view.task_layout, self.widgets,
                    view._connect_task_widget_signals, self.tasks, view.scheduler,
                    video_id, extractor, title_override, insert_into_layout=False,
                    thumbnail_loader=self.thumbnail_loader)
            finally:
                self._discard_unowned_widget(task_id)
                self.request_refresh(order=True, summary=True)

    def _discard_unowned_widget(self, task_id):
        """A failed widget restoration must not leave an entry without a model."""
        if self.tasks.get(task_id) is None:
            widget = self.widgets.pop(task_id, None)
            if widget is not None:
                if self.thumbnail_loader is not None:
                    self.thumbnail_loader.cancel_owner(widget)
                widget.deleteLater()

    def restore(self, task):
        if self.closed:
            return
        if self.tasks.get(task.id) is not None:
            raise ValueError(f'Duplicate task ID: {task.id}')
        view = self.view
        with self.batch():
            try:
                create_restored_task_widget(
                    task, view, view.task_layout, self.widgets, view._connect_task_widget_signals,
                    insert_into_layout=False, thumbnail_loader=self.thumbnail_loader)
                self.tasks.add(task)
                self.last_task_id = max(self.last_task_id, task.id)
            finally:
                self._discard_unowned_widget(task.id)
                self.request_refresh(order=True, summary=True)

    def remove(self, task_id, discard_workspace=True):
        if self.closed:
            return
        view = self.view
        task, widget = self.tasks.get(task_id), self.widgets.get(task_id)
        if widget is None:
            return
        if discard_workspace and task:
            cleanup_request = build_task_cleanup_request(task)
            if task.is_active():
                view.scheduler.cancel_task(task_id)
            view._discard_removed_task_workspace(cleanup_request)
        self.selection.remove_from_selection(task_id)
        if self.thumbnail_loader is not None:
            self.thumbnail_loader.cancel_owner(widget)
        view.task_layout.removeWidget(widget)
        widget.deleteLater()
        del self.widgets[task_id]
        self.tasks.remove(task_id)
        self.request_refresh(order=True, summary=True)

    def load_saved(self):
        view = self.view
        records = view.task_manager.load_tasks()
        if not records or self.closed:
            return
        show_task_list(view.scroll_area, view.empty_label)
        restored, max_id = build_loaded_tasks(records)
        with self.batch():
            for task in restored:
                self.restore(task)
            if loaded_tasks_need_workspace_persistence(records):
                view.task_manager.save_tasks(self.tasks)
            view.total_tasks_in_queue = max(view.total_tasks_in_queue, max_id)
        # Make restored cards visible before the modal resume prompt.
        with self.batch():
            result = handle_paused_task_restore(
                self.tasks, view._confirm_resume_paused_tasks, view.resume_task, view._cleanup_temp_files)
            if result.paused_count:
                self.request_refresh(order=True, summary=True)

    def close(self):
        """Prevent queued callbacks or an unwinding batch from touching closing UI."""
        self.closed = True
        self._order_dirty = self._summary_dirty = False
        if self.thumbnail_loader is not None:
            self.thumbnail_loader.close()
