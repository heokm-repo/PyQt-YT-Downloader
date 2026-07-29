"""Public facade for download subsystem operations."""

from core.download.runner import download_video, download_video_with_result
from core.download.metadata_fetcher import fetch_metadata
from core.download.playlist_extractor import extract_playlist_video_ids

__all__ = (
    "download_video",
    "download_video_with_result",
    "fetch_metadata",
    "extract_playlist_video_ids",
)
