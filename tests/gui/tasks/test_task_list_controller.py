"""Real Qt layouts with lightweight cards; no network or scheduler threads."""
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from PyQt5.QtCore import QCoreApplication, QEvent, Qt
from PyQt5.QtWidgets import QApplication, QLabel, QScrollArea, QVBoxLayout, QWidget

from constants import TaskStatus
from data.models import DownloadTask
from gui.tasks import task_list_controller as module
from gui.tasks.task_actions import TaskActions
from gui.tasks.task_registration import register_download_task
from gui.tasks.task_widget_restore import create_restored_task_widget


class Card(QWidget):
    def __init__(self, task_id, url, settings, parent):
        super().__init__()
        self.task_id = task_id
        self.selected = False
        self.title_label = QLabel(self)
        self.status_label = QLabel(self)
        self.percent_label = QLabel(self)
        self.setFixedHeight(40)

    def update_metadata(self, meta):
        self.title_label.setText(meta.get('title', ''))

    def set_finished(self, **kwargs):
        self.status_label.setText('finished')

    def set_paused(self):
        self.status_label.setText('paused')

    def set_status(self, status):
        self.status_label.setText(status)

    def set_failed(self, message):
        self.status_label.setText(message)


@pytest.fixture
def list_view(monkeypatch):
    app = QApplication.instance() or QApplication([])
    content = QWidget()
    layout = QVBoxLayout(content)
    layout.addStretch()
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(content)
    scroll.resize(600, 300)
    scroll.setAttribute(Qt.WA_DontShowOnScreen, True)
    scroll.show()
    empty, status = QLabel(), QLabel()
    view = SimpleNamespace(
        settings={}, task_layout=layout, scroll_area=scroll, empty_label=empty,
        status_label=status, scheduler=Mock(), _connect_task_widget_signals=Mock(),
        _update_task_counter_ui=Mock(), _discard_removed_task_workspace=Mock(), sort_key='newest')
    view.toggle_enabled = True
    controller = module.TaskListController(view)
    view.task_list = controller
    view.tasks, view.task_widgets = controller.tasks, controller.widgets
    view._sorted_task_ids = Mock(side_effect=lambda: module.sorted_task_ids(view.tasks, view.task_widgets, view.sort_key))
    view.remove_task_from_list = controller.remove
    view.get_task_by_id = controller.tasks.get
    view.update_progress_ui = lambda: controller.request_refresh(order=view.sort_key == 'status', summary=True)
    monkeypatch.setattr(module, 'register_download_task', lambda *a, **kw: register_download_task(*a, widget_factory=Card, **kw))
    monkeypatch.setattr(module, 'create_restored_task_widget', lambda *a, **kw: create_restored_task_widget(*a, widget_factory=Card, **kw))
    try:
        yield app, view, controller
    finally:
        controller.close()
        for widget in controller.widgets.values():
            widget.deleteLater()
        scroll.deleteLater()
        empty.deleteLater()
        status.deleteLater()
        QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
        app.processEvents()


def layout_ids(view):
    return [view.task_layout.itemAt(i).widget().task_id
            for i in range(view.task_layout.count() - 1)]


@pytest.mark.parametrize('size', [100, 1000])
@pytest.mark.parametrize('mode', ['newest', 'oldest', 'status'])
def test_batch_registration_sorts_and_summarizes_once_with_selection(list_view, size, mode):
    _, view, controller = list_view
    view.sort_key = mode
    enqueued = []

    def enqueue(priority, task_id, *args):
        assert controller.tasks.get(task_id) is not None
        assert task_id in controller.widgets
        enqueued.append(task_id)
        # Simulate a scheduler callback while registration is still in a batch.
        controller.tasks.get(task_id).status = list(TaskStatus)[task_id % 5]
        view.update_progress_ui()

    view.scheduler.add_task.side_effect = enqueue
    with patch.object(module, 'summarize_task_progress', wraps=module.summarize_task_progress) as summary, patch.object(
        view.task_layout, 'insertWidget', wraps=view.task_layout.insertWidget
    ) as insert:
        with controller.batch():
            for task_id in range(1, size + 1):
                controller.register(task_id, '', str(task_id), 'youtube')
        assert summary.call_count == 1
        assert insert.call_count == size
    assert view._sorted_task_ids.call_count == 1
    assert enqueued == list(range(1, size + 1))
    assert [task.id for task in controller.tasks] == enqueued
    order = module.sorted_task_ids(controller.tasks, controller.widgets, mode)
    assert layout_ids(view) == controller.visible_order == order
    controller.selection.handle_click(order[0], Qt.NoModifier, controller.widgets, view.task_layout)
    controller.selection.handle_click(order[2], Qt.ShiftModifier, controller.widgets, view.task_layout)
    assert set(controller.selection.get_selected_ids()) == set(order[:3])
    controller.selection.handle_click(order[1], Qt.ControlModifier, controller.widgets, view.task_layout)
    assert set(controller.selection.get_selected_ids()) == {order[0], order[2]}


def test_same_order_does_no_layout_work_and_preserves_scroll_and_selection(list_view):
    app, view, controller = list_view
    with controller.batch():
        for task_id in range(1, 101):
            controller.register(task_id, '')
    app.processEvents()
    # Qt posts child show/layout requests while cards are reparented into a
    # visible scroll area; drain that next event turn before reading its range.
    app.processEvents()
    bar = view.scroll_area.verticalScrollBar()
    assert bar.maximum() > 0
    bar.setValue(bar.maximum() // 2)
    position = bar.value()
    controller.selection.handle_click(80, Qt.NoModifier, controller.widgets, view.task_layout)
    with patch.object(view.task_layout, 'insertWidget', wraps=view.task_layout.insertWidget) as insert, patch.object(
        view.task_layout, 'removeWidget', wraps=view.task_layout.removeWidget
    ) as remove:
        controller.request_refresh(order=True, summary=True)
    app.processEvents()
    assert not insert.called and not remove.called
    assert bar.value() == position
    assert controller.selection.get_selected_ids() == [80]
    assert controller.selection.last_clicked_task_id == 80
    view.sort_key = 'oldest'
    controller.request_refresh(order=True)
    app.processEvents()
    app.processEvents()
    assert layout_ids(view) == list(range(1, 101))
    assert bar.value() == position
    assert controller.selection.get_selected_ids() == [80]
    assert controller.selection.last_clicked_task_id == 80


def test_bulk_removal_has_one_summary_and_keeps_remaining_order(list_view):
    _, view, controller = list_view
    with controller.batch():
        for task_id in range(1, 101):
            controller.register(task_id, '')
    controller.selection.handle_click(70, Qt.NoModifier, controller.widgets, view.task_layout)
    actions = TaskActions(view, controller.batch)
    actions._confirm_question = Mock(return_value=True)
    view._sorted_task_ids.reset_mock()
    with patch.object(module, 'summarize_task_progress', wraps=module.summarize_task_progress) as summary, patch.object(
        view.task_layout, 'insertWidget', wraps=view.task_layout.insertWidget
    ) as insert:
        assert actions.remove_selected_from_list(list(range(1, 81)))
    assert summary.call_count == view._sorted_task_ids.call_count == 1
    assert not insert.called
    assert layout_ids(view) == list(range(100, 80, -1))
    assert [task.id for task in controller.tasks] == list(range(81, 101))
    assert controller.selection.last_clicked_task_id is None
    assert view.scheduler.cancel_task.call_count == 80
    assert view._discard_removed_task_workspace.call_count == 80


def test_nested_batch_recovers_after_mid_registration_failure(list_view, monkeypatch):
    _, view, controller = list_view
    register = module.register_download_task

    def fail_third(task_id, *args, **kwargs):
        if task_id == 3:
            raise RuntimeError('widget construction failed')
        return register(task_id, *args, **kwargs)

    monkeypatch.setattr(module, 'register_download_task', fail_third)
    with pytest.raises(RuntimeError), controller.batch():
        for task_id in range(1, 5):
            controller.register(task_id, '')
    assert controller._batch_depth == 0
    assert layout_ids(view) == [2, 1]
    assert set(controller.widgets) == {task.id for task in controller.tasks} == {1, 2}
    controller.register(4, '')
    assert layout_ids(view) == [4, 2, 1]


def test_restore_batch_keeps_uuid_and_never_enqueues(list_view):
    _, view, controller = list_view
    tasks = [DownloadTask(i, '', status=TaskStatus.FINISHED, meta={'title': '한글'}) for i in (3, 1, 8)]
    with patch.object(module, 'summarize_task_progress', wraps=module.summarize_task_progress) as summary:
        with controller.batch():
            for task in tasks:
                controller.restore(task)
    assert summary.call_count == 1
    assert [task.to_dict() for task in controller.tasks] == [task.to_dict() for task in tasks]
    assert layout_ids(view) == [8, 3, 1]
    assert controller.last_task_id == 8
    view.scheduler.add_task.assert_not_called()


def test_failed_restore_drops_orphan_widget_and_keeps_prior_task(list_view, monkeypatch):
    _, view, controller = list_view
    controller.restore(DownloadTask(1, '', status=TaskStatus.FINISHED))
    restore = module.create_restored_task_widget

    def fail_after_registration(*args, **kwargs):
        restore(*args, **kwargs)
        raise RuntimeError('metadata display failed')

    monkeypatch.setattr(module, 'create_restored_task_widget', fail_after_registration)
    with pytest.raises(RuntimeError), controller.batch():
        controller.restore(DownloadTask(2, '', status=TaskStatus.FINISHED))
    assert controller._batch_depth == 0
    assert set(controller.widgets) == {task.id for task in controller.tasks} == {1}
    assert layout_ids(view) == [1]


def test_bulk_pause_and_resume_coalesce_updates_and_preserve_resume_payload(list_view):
    _, view, controller = list_view
    view.sort_key = 'status'
    with controller.batch():
        for task_id in range(1, 101):
            controller.register(task_id, f'https://example.invalid/{task_id}')
    actions = TaskActions(view, controller.batch)
    view.scheduler.add_task.reset_mock()
    for operation, expected in ((actions.pause_selected, TaskStatus.PAUSED),
                                (actions.resume_selected, TaskStatus.WAITING)):
        with patch.object(module, 'summarize_task_progress', wraps=module.summarize_task_progress) as summary:
            operation(list(range(1, 101)))
        assert summary.call_count == 1
        assert all(task.status == expected for task in controller.tasks)
    assert view.scheduler.pause_task.call_count == 100
    assert view.scheduler.add_task.call_count == 100
    for call in view.scheduler.add_task.call_args_list:
        task = controller.tasks.get(call.args[1])
        assert call.args[0] == 1
        assert call.kwargs['is_resume']
        assert call.args[3]['_workspace_id'] == task.workspace_id


def test_close_during_batch_suppresses_pending_ui_refresh_and_new_registration(list_view):
    _, view, controller = list_view
    with patch.object(module, 'summarize_task_progress', wraps=module.summarize_task_progress) as summary:
        with controller.batch():
            controller.register(1, '')
            controller.close()
            assert controller.register(2, '') is None
        controller.request_refresh(order=True, summary=True)
    assert controller._batch_depth == 0
    assert not summary.called
    assert [task.id for task in controller.tasks] == [1]
    assert view.task_layout.count() == 1


def test_removal_releases_thumbnail_subscription_before_deferred_widget_deletion(list_view):
    _, view, controller = list_view
    controller.register(1, '')
    widget = controller.widgets[1]
    loader = Mock()
    controller.thumbnail_loader = loader
    controller.remove(1)
    loader.cancel_owner.assert_called_once_with(widget)
    controller.close()
    loader.close.assert_called_once()
