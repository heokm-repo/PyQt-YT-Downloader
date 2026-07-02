"""Build duplicate-check inputs from tasks and settings."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from constants import DEFAULT_FORMAT


@dataclass(frozen=True)
class DuplicateCheckTarget:
    extractor: str
    video_id: str
    target_format: str


def duplicate_target_format(settings: Mapping[str, Any] | None) -> str:
    """Return the effective format used for duplicate checks."""
    if not settings:
        return DEFAULT_FORMAT
    return settings.get("format", DEFAULT_FORMAT)


def build_duplicate_check_target_from_values(
    video_id: Optional[str], extractor: Optional[str], settings: Mapping[str, Any] | None
) -> Optional[DuplicateCheckTarget]:
    """Return duplicate-check inputs from raw video metadata."""
    if not video_id:
        return None

    return DuplicateCheckTarget(
        extractor=extractor or "unknown",
        video_id=video_id,
        target_format=duplicate_target_format(settings),
    )


def build_duplicate_check_target(
    task: Any, settings: Mapping[str, Any] | None
) -> Optional[DuplicateCheckTarget]:
    """Return duplicate-check inputs for a task, or None when it has no video ID."""
    return build_duplicate_check_target_from_values(
        getattr(task, "video_id", None),
        getattr(task, "extractor", None),
        settings,
    )