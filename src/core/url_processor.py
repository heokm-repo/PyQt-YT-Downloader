"""URL processing for validation, cleanup, and playlist/video classification across yt-dlp-supported sites."""
from typing import Optional

from utils.utils import validate_url, is_youtube_url
from utils.logger import log
from utils.url_security import redact_url_for_log
from core.youtube_url import _sanitize_url, extract_video_id as get_youtube_video_id, has_video_and_list


class UrlProcessResult:
    """Data class for URL processing results."""
    def __init__(self, clean_url: str, is_playlist: bool, video_id: Optional[str] = None, extractor: Optional[str] = None):
        self.clean_url = clean_url
        self.is_playlist = is_playlist
        self.video_id = video_id
        self.extractor = extractor  # Site identifier, pre-extracted only for YouTube and filled from metadata for others.


class UrlProcessor:
    """Generic URL processor."""

    @staticmethod
    def extract_video_id(url: str) -> Optional[str]:
        """Extract a YouTube video ID while preserving the existing API."""
        return get_youtube_video_id(url)

    @staticmethod
    def requires_playlist_preference(url: str) -> bool:
        """Return whether a YouTube URL needs a playlist/video preference."""
        return bool(url and validate_url(url) and is_youtube_url(url) and has_video_and_list(url))

    @staticmethod
    def process_url(url: str, prefer_playlist: bool = False) -> Optional['UrlProcessResult']:
        """
        Process a URL and return the normalized result.

        Args:
            url: Input URL.
            prefer_playlist: Whether to prefer a playlist when a YouTube URL has both video and list parameters.

        Returns:
            UrlProcessResult, or None if validation fails.
        """
        log.info(f"Processing URL: {redact_url_for_log(url)}")

        if not url or not validate_url(url):
            log.warning(f"Invalid URL detected: {redact_url_for_log(url)}")
            return None

        log.debug("URL validation successful")

        # Existing YouTube playlist/single-video branch logic.
        if is_youtube_url(url):
            return UrlProcessor._process_youtube_url(url, prefer_playlist, log)

        # Other sites are passed through for yt-dlp to handle.
        log.info(
            "Non-YouTube URL detected, passing to yt-dlp: "
            f"{redact_url_for_log(url)}"
        )
        return UrlProcessResult(url, is_playlist=False, video_id=None, extractor=None)

    @staticmethod
    def _process_youtube_url(url: str, prefer_playlist: bool, log) -> Optional['UrlProcessResult']:
        """Handle YouTube-specific URL processing."""
        clean_url, is_playlist = _sanitize_url(url, prefer_playlist=prefer_playlist)
        log.debug(
            f"Sanitized URL: {redact_url_for_log(clean_url)}, "
            f"is_playlist: {is_playlist}"
        )

        # Extract video_id for single-video URLs.
        video_id = None
        if not is_playlist:
            video_id = UrlProcessor.extract_video_id(clean_url)
            log.debug(f"Extracted video_id: {video_id}")

        return UrlProcessResult(clean_url, is_playlist, video_id, extractor='youtube')
