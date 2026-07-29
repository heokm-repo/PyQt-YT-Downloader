"""Non-blocking wait policy for replacing an active duplicate task."""

from __future__ import annotations

from typing import Any, Callable


DUPLICATE_STOP_POLL_MS = 250
DUPLICATE_STOP_MAX_ATTEMPTS = 40


def wait_for_task_stop(
    scheduler: Any,
    task_id: int,
    schedule_once: Callable[[int, Callable[[], None]], None],
    on_stopped: Callable[[], None],
    on_timeout: Callable[[], None],
    *,
    attempts_left: int = DUPLICATE_STOP_MAX_ATTEMPTS,
) -> None:
    """Poll scheduler ownership asynchronously until a task stops."""
    if not scheduler.is_task_running(task_id):
        on_stopped()
        return
    if attempts_left <= 0:
        on_timeout()
        return
    schedule_once(
        DUPLICATE_STOP_POLL_MS,
        lambda: wait_for_task_stop(
            scheduler,
            task_id,
            schedule_once,
            on_stopped,
            on_timeout,
            attempts_left=attempts_left - 1,
        ),
    )
