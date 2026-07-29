"""Planning helpers for single-video downloads."""

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

from gui.tasks.duplicate_check_target import (
    DuplicateCheckTarget,
    build_duplicate_check_target_from_values,
)


@dataclass(frozen=True)
class SingleVideoDownloadPlan:
    clean_url: str
    video_id: Optional[str]
    extractor: str
    settings: dict
    duplicate_target: Optional[DuplicateCheckTarget]


@dataclass(frozen=True)
class SingleVideoDuplicateDecision:
    cancelled: bool
    duplicate_task: Any | None = None


def build_single_video_download_plan(
    clean_url: str,
    video_id: Optional[str],
    extractor: Optional[str],
    settings: Mapping[str, Any],
) -> SingleVideoDownloadPlan:
    """Return normalized inputs needed to register a single-video download."""
    current_settings = dict(settings)
    effective_extractor = extractor or "unknown"
    return SingleVideoDownloadPlan(
        clean_url=clean_url,
        video_id=video_id,
        extractor=effective_extractor,
        settings=current_settings,
        duplicate_target=build_duplicate_check_target_from_values(
            video_id,
            effective_extractor,
            current_settings,
        ),
    )


def review_single_video_duplicate(
    duplicate_checker: Any,
    duplicate_target: Optional[DuplicateCheckTarget],
    tasks: Sequence[Any],
    confirm_duplicate: Callable[[str], bool] | None = None,
) -> SingleVideoDuplicateDecision:
    """Return the confirmation result and any active duplicate task."""
    if not duplicate_target:
        return SingleVideoDuplicateDecision(False)

    is_duplicate, message, duplicate_task = duplicate_checker.is_duplicate(
        duplicate_target.extractor,
        duplicate_target.video_id,
        -1,
        list(tasks),
        duplicate_target.target_format,
    )
    if not is_duplicate:
        return SingleVideoDuplicateDecision(False)

    if confirm_duplicate is None:
        return SingleVideoDuplicateDecision(True, duplicate_task)

    return SingleVideoDuplicateDecision(
        not confirm_duplicate(message),
        duplicate_task,
    )


def single_video_duplicate_cancelled(
    duplicate_checker: Any,
    duplicate_target: Optional[DuplicateCheckTarget],
    tasks: Sequence[Any],
    confirm_duplicate: Callable[[str], bool] | None = None,
) -> bool:
    """Compatibility wrapper returning only the cancellation decision."""
    return review_single_video_duplicate(
        duplicate_checker,
        duplicate_target,
        tasks,
        confirm_duplicate,
    ).cancelled
