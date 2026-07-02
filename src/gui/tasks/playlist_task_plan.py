"""Build playlist task registration plans for the main window."""

from dataclasses import dataclass
from typing import Iterable, List

from constants import PLAYLIST_VIDEO_URL_TEMPLATE


@dataclass(frozen=True)
class PlaylistTaskPlan:
    video_id: str
    url: str
    title_override: str
    extractor: str = "youtube"


def build_playlist_task_plans(
    video_ids: Iterable[str],
    title_template: str,
    url_template: str = PLAYLIST_VIDEO_URL_TEMPLATE,
) -> List[PlaylistTaskPlan]:
    """Create the task registration data needed for playlist videos."""
    return [
        PlaylistTaskPlan(
            video_id=video_id,
            url=url_template.format(video_id=video_id),
            title_override=title_template.format(video_id=video_id),
        )
        for video_id in video_ids
    ]

def select_playlist_registration_ids(
    video_ids: Iterable[str],
    filtered_ids: Iterable[str],
    duplicate_count: int,
    exclude_duplicates: bool,
) -> List[str]:
    """Choose which playlist IDs should be registered after duplicate review."""
    if duplicate_count > 0 and not exclude_duplicates:
        return list(video_ids)
    return list(filtered_ids)
