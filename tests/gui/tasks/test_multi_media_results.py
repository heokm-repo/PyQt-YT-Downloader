from types import SimpleNamespace
from unittest.mock import Mock, patch

from constants import TaskStatus
from core.task_metadata import apply_metadata_to_task
from data.models import DownloadTask
from gui.tasks.download_completion import (
    persist_download_output, record_completed_media, task_output_paths,
)
from gui.tasks.task_actions import TaskActions
from gui.tasks.task_file_delete import DeleteFileResult, DeleteFileStatus
from gui.tasks.task_resume_plan import build_resume_task_plan
from gui.tasks.task_widget_restore import restore_task_widget_state


def make_task(tmp_path):
    files = [tmp_path / 'first.mp4', tmp_path / 'second.mp4']
    for index, path in enumerate(files):
        path.write_bytes(b'video' * (index + 1))
    items = [{'id': str(i), 'extractor': 'twitter', 'title': 'same', 'kind': 'media',
              'state': 'completed', 'output_path': str(path)} for i, path in enumerate(files)]
    items.append({'id': 'photo', 'kind': 'image', 'state': 'skipped'})
    task = DownloadTask(1, 'https://x.com/post', settings={'format': 'mp4'})
    apply_metadata_to_task(task, {'id': 'post', 'extractor': 'twitter', 'media_items': items,
                                  'output_paths': [str(p) for p in files]})
    return task, files


def test_partial_outputs_round_trip_and_individual_history(tmp_path):
    task, paths = make_task(tmp_path)
    task.meta['media_items'].append({'id': 'failed', 'kind': 'media', 'state': 'failed'})
    task.status = TaskStatus.FAILED
    restored = DownloadTask.from_dict(task.to_dict())
    assert task_output_paths(restored) == [str(p) for p in paths]
    assert restored.output_path == str(paths[0])
    plan = build_resume_task_plan(restored, {})
    assert '_resume_output_path' not in plan.settings
    history = Mock()
    record_completed_media(restored, history)
    assert [call.args[1] for call in history.add_to_history.call_args_list] == ['0', '1']


def test_total_size_and_restored_summary_include_all_outputs(tmp_path):
    task, paths = make_task(tmp_path)
    persist_download_output(task, str(paths[0]), True)
    assert task.meta['file_size'] == 15
    task.status = TaskStatus.FINISHED
    widget = Mock()
    restore_task_widget_state(widget, task)
    widget.set_finished.assert_called_once_with(file_size=15)
    assert widget.status_label.setText.called


def test_delete_removes_every_result_before_removing_task(tmp_path):
    task, paths = make_task(tmp_path)
    window = SimpleNamespace(get_task_by_id=Mock(return_value=task), remove_task_from_list=Mock())
    TaskActions(window).delete_file(1, confirm=False)
    assert not any(path.exists() for path in paths)
    window.remove_task_from_list.assert_called_once_with(1)


def test_failed_second_delete_retains_task(tmp_path):
    task, _ = make_task(tmp_path)
    window = SimpleNamespace(get_task_by_id=Mock(return_value=task), remove_task_from_list=Mock())
    actions = TaskActions(window)
    actions._show_warning = Mock()
    with patch('gui.tasks.task_actions.delete_output_file', side_effect=[
        DeleteFileResult(DeleteFileStatus.DELETED), DeleteFileResult(DeleteFileStatus.PERMISSION_ERROR),
    ]) as delete:
        actions.delete_file(1, confirm=False)
    assert delete.call_count == 2
    window.remove_task_from_list.assert_not_called()
