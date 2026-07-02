"""Playlist filtering helpers."""

from typing import Protocol, Sequence


class HistoryLookup(Protocol):
    def is_downloaded(self, extractor: str, video_id: str, target_format: str) -> bool:
        ...


def filter_duplicate_videos(
    video_ids: Sequence[str],
    history_manager: HistoryLookup,
    tasks: Sequence[object],
    target_format: str,
    extractor: str = "youtube",
) -> tuple[list[str], int]:
    """Filter playlist videos already downloaded or queued for the same format."""
    duplicate_count = 0
    filtered_ids: list[str] = []

    for video_id in video_ids:
        if history_manager.is_downloaded(extractor, video_id, target_format):
            duplicate_count += 1
            continue

        if _is_queued_duplicate(tasks, extractor, video_id, target_format):
            duplicate_count += 1
            continue

        filtered_ids.append(video_id)

    return filtered_ids, duplicate_count


def _is_queued_duplicate(
    tasks: Sequence[object],
    extractor: str,
    video_id: str,
    target_format: str,
) -> bool:
    return any(
        getattr(task, "extractor", None) == extractor
        and getattr(task, "video_id", None) == video_id
        and (getattr(task, "settings", {}) or {}).get("format", "mp4") == target_format
        and task.is_active()
        for task in tasks
    )
