import pytest

from constants import TaskStatus
from data.models import DownloadTask
from data.task_collection import TaskCollection
from gui.tasks.task_load_plan import build_loaded_tasks


def test_add_remove_lookup_and_snapshots_keep_insertion_order():
    first, second, third = [DownloadTask(i, '') for i in (7, 2, 10)]
    tasks = TaskCollection([first, second])
    snapshot = tasks.snapshot()
    iterator = iter(tasks)
    tasks.add(third)
    assert tasks.remove(7) is first
    assert list(iterator) == [first, second]
    assert snapshot == (first, second)
    assert tasks.snapshot() == (second, third)
    assert tasks.get(2) is second
    assert tasks.get(7) is None
    assert tasks.remove(7) is None
    second.status = TaskStatus.FINISHED
    assert tasks.get(2).status == TaskStatus.FINISHED
    assert len(tasks) == 2


def test_duplicate_id_does_not_replace_existing_task():
    original = DownloadTask(1, 'first')
    tasks = TaskCollection([original])
    with pytest.raises(ValueError):
        tasks.add(DownloadTask(1, 'replacement'))
    assert tasks.snapshot() == (original,)
    assert tasks.get(1) is original


def test_restore_uses_validated_ids_and_preserves_source_order():
    restored, max_id = build_loaded_tasks([{'id': 10}, {'id': 3}, {'id': 10}, {'id': 'bad'}, {'id': 5}])
    tasks = TaskCollection(restored)
    assert [task.id for task in tasks] == [10, 3, 5]
    assert max_id == 10
    for task in restored:
        assert tasks.get(task.id) is task
