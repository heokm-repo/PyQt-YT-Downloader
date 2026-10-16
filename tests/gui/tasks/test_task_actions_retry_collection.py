from types import SimpleNamespace
from unittest.mock import Mock, patch

from constants import TaskStatus
from data.models import DownloadTask
from data.task_collection import TaskCollection
from gui.tasks.task_actions import TaskActions


def test_completed_retry_accepts_collection_without_list_slicing():
    task = DownloadTask(1, 'https://example.invalid/watch', status=TaskStatus.FINISHED,
                        video_id='id', extractor='Example')
    tasks = TaskCollection([task])
    view = SimpleNamespace(toggle_enabled=True, tasks=tasks, settings={'format': 'mp4'},
                           get_task_by_id=tasks.get, history_manager=Mock(),
                           remove_task_from_list=Mock(), url_input=Mock(),
                           start_download=Mock(), update_progress_ui=Mock())
    with patch('gui.tasks.task_actions.should_continue_retry_after_duplicate_check', return_value=True) as review:
        TaskActions(view).retry_task(1)
    assert review.call_args.args[2] == (task,)
    view.remove_task_from_list.assert_called_once_with(1, discard_workspace=False)
    view.url_input.setText.assert_called_once_with(task.url)
    view.start_download.assert_called_once_with()
