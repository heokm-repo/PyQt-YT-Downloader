from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from gui.tasks.task_actions import TaskActions
from gui.tasks.task_file_delete import DeleteFileResult, DeleteFileStatus


@pytest.mark.parametrize("status, removed", [
    (DeleteFileStatus.PERMISSION_ERROR, False),
    (DeleteFileStatus.ERROR, False),
    (DeleteFileStatus.NOT_FILE, False),
    (DeleteFileStatus.DELETED, True),
    (DeleteFileStatus.MISSING, True),
])
def test_delete_only_removes_card_when_file_is_gone(status, removed):
    window = SimpleNamespace(
        get_task_by_id=Mock(return_value=SimpleNamespace(output_path="file.mp4")),
        remove_task_from_list=Mock(),
    )
    actions = TaskActions(window)
    actions._show_warning = Mock()
    with patch("gui.tasks.task_actions.delete_output_file", return_value=DeleteFileResult(status)):
        actions.delete_file(7, confirm=False)
    assert window.remove_task_from_list.called is removed
