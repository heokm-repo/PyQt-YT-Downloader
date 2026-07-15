"""Playlist extraction helpers backed by yt-dlp."""

from core.download.options import _build_playlist_extract_options
from core.youtube_url import _sanitize_url
from core.ytdlp.wrapper import YtDlpWrapper
from locales.strings import STR
from utils.bin.manager import get_ytdlp_path
from utils.logger import log


def extract_playlist_video_ids(url):
    """Extract video IDs from a playlist URL using yt-dlp flat playlist data."""
    clean_url, is_playlist = _sanitize_url(url, prefer_playlist=True)

    if not is_playlist:
        return [], False, STR.ERR_NOT_PLAYLIST

    ytdlp_path = get_ytdlp_path()
    if not ytdlp_path:
        return [], False, STR.ERR_YTDLP_MISSING

    try:
        wrapper = YtDlpWrapper(ytdlp_path)
        info, success = wrapper.extract_info(
            clean_url,
            download=False,
            options=_build_playlist_extract_options(url=clean_url),
        )

        if not success or not info:
            return [], False, STR.ERR_CANNOT_FETCH_INFO

        entries = _get_playlist_entries(info)
        if entries is None:
            return [], False, STR.ERR_NOT_PLAYLIST

        return extract_entry_ids(entries), True, ""
    except Exception as exc:
        log.error(f"Playlist Error: {exc}", exc_info=True)
        return [], False, str(exc)


def _get_playlist_entries(info):
    if info.get("_type") == "playlist":
        return info.get("entries", [])
    if "entries" in info:
        return info["entries"]
    return None


def extract_entry_ids(entries):
    ids = [entry.get("id") or entry.get("url", "").split("=")[-1] for entry in entries if entry]
    return [video_id for video_id in ids if video_id]
