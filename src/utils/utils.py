from typing import Optional
from urllib.parse import urlparse

from utils.app_paths import get_base_path, get_user_data_path

def get_ffmpeg_path() -> Optional[str]:
    """Return the managed external FFmpeg executable path."""
    from utils.bin.manager import get_ffmpeg_path as get_bin_ffmpeg
    return get_bin_ffmpeg()

def validate_url(url: str) -> bool:
    """Validate URLs by allowing any http or https URL supported by yt-dlp."""
    if not url:
        return False
    try:
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except (AttributeError, TypeError, ValueError):
        return False

def is_youtube_url(url: str) -> bool:
    """Return whether the URL is a YouTube URL for YouTube-specific branching."""
    if not url:
        return False

    try:
        host = (urlparse(str(url)).hostname or "").lower().rstrip(".")
    except (AttributeError, TypeError, ValueError):
        return False

    return (
        host == "youtube.com"
        or host.endswith(".youtube.com")
        or host == "youtu.be"
    )

def format_bytes(b) -> str:
    """Format bytes as a human-readable string."""
    if b is None:
        return "0 B"
    
    try:
        b = float(b)
    except (ValueError, TypeError):
        return "? B"
        
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024.0
        i += 1
    return f"{b:.2f} {units[i]}"
