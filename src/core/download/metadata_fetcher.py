"""Metadata fetching helpers backed by yt-dlp."""

from core.download.options import _build_metadata_extract_options
from core.download.metadata_mapper import build_metadata_result
from core.youtube_url import _sanitize_url
from core.ytdlp.wrapper import YtDlpWrapper
from utils.bin.manager import get_ytdlp_path
from utils.logger import log
from utils.utils import is_youtube_url


def fetch_metadata(url, settings=None):
    """Fetch and map metadata for a supported yt-dlp URL."""
    if is_youtube_url(url):
        clean_url, is_playlist = _sanitize_url(url)
    else:
        clean_url = url
        is_playlist = False

    if not clean_url:
        return {}, False

    ytdlp_path = get_ytdlp_path()
    if not ytdlp_path:
        return {}, False

    try:
        wrapper = YtDlpWrapper(ytdlp_path)
        options = _build_metadata_extract_options(settings, is_playlist, url=clean_url)
        info, success = wrapper.extract_info(clean_url, download=False, options=options)

        if not success or not info:
            return {}, False

        return build_metadata_result(info, clean_url, is_playlist), True
    except Exception as exc:
        log.error(f"Metadata Error: {exc}", exc_info=True)
        return {}, False
