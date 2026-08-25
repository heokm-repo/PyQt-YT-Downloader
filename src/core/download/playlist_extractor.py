"""Playlist extraction helpers backed by yt-dlp."""

from core.download.options import _build_playlist_extract_options
from core.youtube_url import _sanitize_url
from core.ytdlp.wrapper import YtDlpWrapper
from locales.strings import STR
from utils.bin.manager import get_ytdlp_path
from utils.logger import log


def extract_playlist_video_ids(url):
    """Return video IDs, success, error text, and the raw playlist entry count."""
    clean_url, is_playlist = _sanitize_url(url, prefer_playlist=True)

    if not is_playlist:
        return [], False, STR.ERR_NOT_PLAYLIST, 0

    ytdlp_path = get_ytdlp_path()
    if not ytdlp_path:
        return [], False, STR.ERR_YTDLP_MISSING, 0

    try:
        wrapper = YtDlpWrapper(ytdlp_path)
        info, success = wrapper.extract_info(
            clean_url,
            options=_build_playlist_extract_options(url=clean_url),
        )

        if not success or not info:
            return [], False, STR.ERR_CANNOT_FETCH_INFO, 0

        entries = _get_playlist_entries(info)
        if entries is None:
            return [], False, STR.ERR_NOT_PLAYLIST, 0

        return extract_entry_ids(entries), True, "", len(entries)
    except Exception as exc:
        log.error(f"Playlist Error: {exc}", exc_info=True)
        return [], False, str(exc), 0


def _get_playlist_entries(info):
    if info.get("_type") == "playlist":
        return info.get("entries", [])
    if "entries" in info:
        return info["entries"]
    return None


def extract_entry_ids(entries):
    ids = [entry.get("id") or entry.get("url", "").split("=")[-1] for entry in entries if entry]
    return [video_id for video_id in ids if video_id]
