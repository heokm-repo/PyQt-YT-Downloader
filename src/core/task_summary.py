"""Task progress summary helpers."""

from dataclasses import dataclass
from typing import Protocol, Sequence

from constants import TaskStatus


class TaskLike(Protocol):
    status: TaskStatus

    def is_active(self) -> bool:
        ...


@dataclass(frozen=True)
class TaskProgressSummary:
    total: int
    finished: int
    failed: int
    in_progress: int

    @property
    def has_failures(self) -> bool:
        return self.failed > 0


def summarize_task_progress(tasks: Sequence[TaskLike]) -> TaskProgressSummary:
    finished = 0
    failed = 0
    in_progress = 0

    for task in tasks:
        if task.status == TaskStatus.FINISHED:
            finished += 1
        elif task.status == TaskStatus.FAILED:
            failed += 1
        elif task.is_active():
            in_progress += 1

    return TaskProgressSummary(
        total=len(tasks),
        finished=finished,
        failed=failed,
        in_progress=in_progress,
    )
