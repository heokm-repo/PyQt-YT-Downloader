"""Playlist filtering helpers."""

from typing import Iterable, Protocol, Sequence

from data.duplicate_checker import active_duplicate_keys


class HistoryLookup(Protocol):
    def find_downloaded_ids(self, extractor: str, video_ids: Sequence[str], target_format: str) -> set[str]:
        ...


def filter_duplicate_videos(
    video_ids: Sequence[str],
    history_manager: HistoryLookup,
    tasks: Iterable[object],
    target_format: str,
    extractor: str = "youtube",
) -> tuple[list[str], int]:
    """Filter playlist videos already downloaded or queued for the same format."""
    if not video_ids:
        return [], 0
    downloaded = history_manager.find_downloaded_ids(extractor, video_ids, target_format)
    candidates = [video_id for video_id in video_ids if video_id not in downloaded]
    if not candidates:
        return [], len(video_ids)
    active = active_duplicate_keys(tasks)
    # Do not add accepted IDs to active: repeated new inputs retain their order
    # and multiplicity, exactly as in the per-video implementation.
    filtered_ids = [video_id for video_id in candidates
                    if (extractor, video_id, target_format) not in active]
    return filtered_ids, len(video_ids) - len(filtered_ids)
