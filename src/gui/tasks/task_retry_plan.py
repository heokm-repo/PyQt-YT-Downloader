"""Retry planning helpers for task actions."""

from dataclasses import dataclass
from typing import Any, Callable, Optional, Sequence

from locales.strings import STR
from gui.dialogs.messages import ask_question
from gui.tasks.duplicate_check_target import DuplicateCheckTarget, build_duplicate_check_target


@dataclass(frozen=True)
class RetryTaskPlan:
    url: str
    duplicate_target: Optional[DuplicateCheckTarget] = None


def build_retry_task_plan(task: Any, settings: dict) -> Optional[RetryTaskPlan]:
    """Return retry inputs for a task, or None when retry cannot start."""
    if not task:
        return None

    url = getattr(task, "url", "")
    if not url:
        return None

    return RetryTaskPlan(
        url=url,
        duplicate_target=build_duplicate_check_target(task, settings),
    )


def should_continue_retry_after_duplicate_check(
    duplicate_target: Optional[DuplicateCheckTarget],
    task_id: int,
    tasks: Sequence[Any],
    history_manager: Any,
    parent_widget: Any,
    duplicate_checker_factory: Optional[Callable[[Any], Any]] = None,
    confirm_duplicate: Optional[Callable[[str], bool]] = None,
) -> bool:
    """Return True when retry should continue after optional duplicate checking."""
    if not duplicate_target:
        return True

    if duplicate_checker_factory is None:
        from data.managers import DuplicateChecker

        duplicate_checker_factory = DuplicateChecker

    duplicate_checker = duplicate_checker_factory(history_manager)
    is_duplicate, message, _duplicate_task = duplicate_checker.is_duplicate(
        duplicate_target.extractor,
        duplicate_target.video_id,
        task_id,
        list(tasks),
        duplicate_target.target_format,
    )

    if is_duplicate:
        confirm = confirm_duplicate or (
            lambda duplicate_message: ask_question(parent_widget, STR.MSG_DUPLICATE_CHECK, duplicate_message)
        )
        if not confirm(message):
            return False

    history_manager.remove_from_history(
        duplicate_target.extractor,
        duplicate_target.video_id,
        duplicate_target.target_format,
    )
    return True