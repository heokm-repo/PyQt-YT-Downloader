from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from data.models import DownloadTask
from data.task_collection import TaskCollection
from gui.tasks.task_registration import register_download_task
from gui.tasks.task_list_controller import TaskListController
from gui.windows.main_window import YTDownloaderPyQt5


def test_duplicate_registration_fails_before_widget_or_scheduler_side_effects():
    tasks = TaskCollection([DownloadTask(1, '')])
    scheduler, factory = Mock(), Mock()
    widgets = {}
    with pytest.raises(ValueError):
        register_download_task(1, '', {}, None, Mock(), widgets, Mock(), tasks, scheduler,
                               widget_factory=factory)
    factory.assert_not_called()
    scheduler.add_task.assert_not_called()
    assert widgets == {}


def test_registration_is_indexed_before_scheduler_can_emit_events():
    tasks = TaskCollection()
    scheduler = Mock()
    widgets = {}
    observed = []

    def enqueue(priority, task_id, *args):
        observed.append((tasks.get(task_id), task_id in widgets))

    scheduler.add_task.side_effect = enqueue
    task = register_download_task(2, '', {}, None, Mock(), widgets, Mock(), tasks, scheduler,
                                  widget_factory=lambda *args: Mock())
    assert observed == [(task, True)]


def test_main_window_restore_indexes_every_valid_task_before_resume():
    records = [{'id': 8, 'status': 'paused'}, {'id': 3, 'status': 'finished'}, {'id': 8}]
    tasks = TaskCollection()
    window = SimpleNamespace(
        task_manager=Mock(), tasks=tasks, scroll_area=Mock(), empty_label=Mock(),
        task_layout=Mock(), task_widgets={}, _connect_task_widget_signals=Mock(),
        _apply_task_sort_order=Mock(), total_tasks_in_queue=0, update_progress_ui=Mock(),
        _confirm_resume_paused_tasks=lambda: True, resume_task=Mock(), _cleanup_temp_files=Mock())
    window.task_manager.load_tasks.return_value = records
    window.task_list = TaskListController(window)
    tasks = window.task_list.tasks
    window.tasks = tasks
    window.task_widgets = window.task_list.widgets
    window._sorted_task_ids = lambda: []
    window.status_label = Mock()
    window._update_task_counter_ui = Mock()
    observed = []
    window.resume_task.side_effect = lambda task_id: observed.append(tasks.get(task_id))
    with patch('gui.tasks.task_list_controller.create_restored_task_widget') as widget:
        YTDownloaderPyQt5.load_tasks_from_file(window)
    assert [task.id for task in tasks] == [8, 3]
    assert widget.call_count == 2
    assert window.total_tasks_in_queue == 8
    assert observed == [tasks.get(8)]
    assert observed[0] is not None
    assert YTDownloaderPyQt5.get_task_by_id(window, 3) is tasks.get(3)
    assert YTDownloaderPyQt5.get_task_by_id(window, 999) is None
