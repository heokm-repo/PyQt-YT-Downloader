from unittest.mock import patch

from data import managers


def test_failed_task_replacement_preserves_previous_list(tmp_path):
    with patch.object(managers, 'get_user_data_path', return_value=str(tmp_path)):
        manager = managers.TaskManager()
    from pathlib import Path
    destination = Path(manager.tasks_file)
    original = b'[{"id": "existing"}]\n'
    destination.write_bytes(original)
    with patch('utils.json_store.os.replace', side_effect=PermissionError('locked')), patch.object(managers, 'log') as log:
        manager.save_tasks([])
    assert destination.read_bytes() == original
    log.error.assert_called_once()
