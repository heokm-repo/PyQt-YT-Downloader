"""Decide which playlist videos should be registered."""

from dataclasses import dataclass
from typing import Callable, Iterable, List

from gui.tasks.playlist_task_plan import select_playlist_registration_ids


@dataclass(frozen=True)
class PlaylistRegistrationDecision:
    video_ids: List[str]
    duplicate_count: int
    exclude_duplicates: bool

    @property
    def has_videos(self) -> bool:
        return bool(self.video_ids)


def build_playlist_registration_decision(
    video_ids: Iterable[str],
    filtered_ids: Iterable[str],
    duplicate_count: int,
    ask_exclude_duplicates: Callable[[int, int], bool],
) -> PlaylistRegistrationDecision:
    """Return final playlist video IDs after duplicate review."""
    all_ids = list(video_ids)
    filtered_id_list = list(filtered_ids)
    exclude_duplicates = True

    if duplicate_count > 0:
        exclude_duplicates = ask_exclude_duplicates(len(all_ids), duplicate_count)

    selected_ids = select_playlist_registration_ids(
        all_ids,
        filtered_id_list,
        duplicate_count,
        exclude_duplicates,
    )
    return PlaylistRegistrationDecision(
        video_ids=selected_ids,
        duplicate_count=duplicate_count,
        exclude_duplicates=exclude_duplicates,
    )
