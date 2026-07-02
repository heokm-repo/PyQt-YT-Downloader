"""Helpers for stopping Qt-style worker objects."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class WorkerStopStatus(Enum):
    NOT_RUNNING = "not_running"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True)
class WorkerStopResult:
    status: WorkerStopStatus

    @property
    def timed_out(self) -> bool:
        return self.status == WorkerStopStatus.TIMED_OUT


def stop_running_worker(worker: Any, wait_ms: int) -> WorkerStopResult:
    """Terminate a running worker and report whether it stopped in time."""
    if not worker or not worker.isRunning():
        return WorkerStopResult(WorkerStopStatus.NOT_RUNNING)

    worker.terminate()
    if worker.wait(wait_ms):
        return WorkerStopResult(WorkerStopStatus.STOPPED)

    return WorkerStopResult(WorkerStopStatus.TIMED_OUT)