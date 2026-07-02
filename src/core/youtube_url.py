"""YouTube URL normalization helpers."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from constants import DOMAIN_YOUTU_BE, YOUTUBE_PLAYLIST_URL_PREFIX, YOUTUBE_SHORTS_PATH
from utils.utils import is_youtube_url


def _has_path_video(parsed) -> bool:
    return (
        parsed.netloc.endswith(DOMAIN_YOUTU_BE)
        and bool(parsed.path)
        and parsed.path != "/"
        and not parsed.path.startswith(YOUTUBE_SHORTS_PATH)
    )


def _sanitize_url(url, prefer_playlist=False):
    """Normalize a YouTube URL and classify it as a playlist or single video."""
    if not url:
        return "", False

    if not is_youtube_url(url):
        return url, False

    url = str(url)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    has_video = "v" in qs or _has_path_video(parsed)

    if parsed.path and YOUTUBE_SHORTS_PATH in parsed.path:
        return url, False

    if has_video and "list" in qs:
        if prefer_playlist:
            return f"{YOUTUBE_PLAYLIST_URL_PREFIX}{qs['list'][0]}", True

        del qs["list"]
        new_query = urlencode(qs, doseq=True)
        return urlunparse(parsed._replace(query=new_query)), False

    if "list" in qs and not has_video:
        return url, True

    return url, False


def has_video_and_list(url):
    """Return True when a YouTube URL contains both video and playlist IDs."""
    if not url or not is_youtube_url(url):
        return False

    parsed = urlparse(str(url))
    qs = parse_qs(parsed.query)
    has_video = "v" in qs or _has_path_video(parsed)

    return has_video and "list" in qs and YOUTUBE_SHORTS_PATH not in (parsed.path or "")

def extract_video_id(url: str):
    """Extract a YouTube video ID from watch and youtu.be URLs."""
    if not url or not is_youtube_url(url):
        return None

    try:
        parsed = urlparse(str(url))
        qs = parse_qs(parsed.query)

        if "v" in qs:
            return qs.get("v", [None])[0]

        if parsed.netloc.endswith(DOMAIN_YOUTU_BE) and parsed.path:
            video_id = parsed.path.strip("/")
            return video_id or None

        return None
    except (ValueError, KeyError):
        return None
