"""
URL 처리 전담 클래스
URL 검증, 정제, 플레이리스트/비디오 구분 등의 로직을 담당
범용 URL 지원 (YouTube + 기타 yt-dlp 지원 사이트)
"""
from typing import Optional

from utils.utils import validate_url, is_youtube_url
from core.youtube_url import _sanitize_url, extract_video_id as get_youtube_video_id, has_video_and_list


class UrlProcessResult:
    """URL 처리 결과를 담는 데이터 클래스"""
    def __init__(self, clean_url: str, is_playlist: bool, video_id: Optional[str] = None, extractor: Optional[str] = None):
        self.clean_url = clean_url
        self.is_playlist = is_playlist
        self.video_id = video_id
        self.extractor = extractor  # 사이트 식별자 (YouTube일 때만 사전 추출, 나머지는 메타데이터에서)


class UrlProcessor:
    """URL 처리 전담 클래스 (범용)"""

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
        URL을 처리하고 결과 반환 (범용)

        Args:
            url: 입력된 URL
            prefer_playlist: YouTube URL에 video/list가 함께 있을 때 플레이리스트를 선택할지 여부

        Returns:
            UrlProcessResult 또는 None (검증 실패 시)
        """
        from utils.logger import log

        log.info(f"Processing URL: {url}")

        if not url or not validate_url(url):
            log.warning(f"Invalid URL detected: {url}")
            return None

        log.debug("URL validation successful")

        # YouTube URL인 경우: 기존 플레이리스트/단일 영상 분기 로직
        if is_youtube_url(url):
            return UrlProcessor._process_youtube_url(url, prefer_playlist, log)

        # 기타 사이트: URL을 그대로 사용 (yt-dlp가 처리)
        log.info(f"Non-YouTube URL detected, passing to yt-dlp: {url}")
        return UrlProcessResult(url, is_playlist=False, video_id=None, extractor=None)

    @staticmethod
    def _process_youtube_url(url: str, prefer_playlist: bool, log) -> Optional['UrlProcessResult']:
        """YouTube URL 전용 처리 로직"""
        clean_url, is_playlist = _sanitize_url(url, prefer_playlist=prefer_playlist)
        log.debug(f"Sanitized URL: {clean_url}, is_playlist: {is_playlist}")

        # video_id 추출 (단일 영상인 경우)
        video_id = None
        if not is_playlist:
            video_id = UrlProcessor.extract_video_id(clean_url)
            log.debug(f"Extracted video_id: {video_id}")

        return UrlProcessResult(clean_url, is_playlist, video_id, extractor='youtube')