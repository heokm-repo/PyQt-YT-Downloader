"""Public facade for download subsystem operations."""

from core.download.runner import download_video_with_result
from core.download.playlist_extractor import extract_playlist_video_ids

__all__ = (
    "download_video_with_result",
    "extract_playlist_video_ids",
)
