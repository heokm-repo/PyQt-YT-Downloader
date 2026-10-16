"""GUI-owned task membership in insertion order, indexed by stable task ID."""
from collections.abc import Iterable, Iterator

from data.models import DownloadTask


class TaskCollection:
    """One ordered dictionary owns membership; snapshots share live task objects.

    Task IDs must remain unchanged after insertion. Status/metadata can change;
    active duplicate keys are deliberately not cached here.
    """
    def __init__(self, tasks: Iterable[DownloadTask] = ()):
        self._by_id: dict[int, DownloadTask] = {}
        for task in tasks:
            self.add(task)

    def add(self, task: DownloadTask) -> None:
        if task.id in self._by_id:
            raise ValueError(f'Duplicate task ID: {task.id}')
        self._by_id[task.id] = task

    def remove(self, task_id: int) -> DownloadTask | None:
        return self._by_id.pop(task_id, None)

    def get(self, task_id: int) -> DownloadTask | None:
        return self._by_id.get(task_id)

    def snapshot(self) -> tuple[DownloadTask, ...]:
        return tuple(self._by_id.values())

    def __iter__(self) -> Iterator[DownloadTask]:
        return iter(self.snapshot())

    def __len__(self) -> int:
        return len(self._by_id)
