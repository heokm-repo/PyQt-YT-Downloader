import sys
import os
import re
from typing import Optional
from constants import (
    APPDATA_DIR_NAME,
    APPDATA_ENV_VAR,
    YOUTUBE_URL_PATTERNS
)


def get_base_path() -> str:
    """Return the base path of the executable, compatible with PyInstaller."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_path() -> str:
    """Return the Windows app data directory used by this application."""
    base_path = os.getenv(APPDATA_ENV_VAR)
    if not base_path:
        return get_base_path()

    data_path = os.path.join(base_path, APPDATA_DIR_NAME)

    if not os.path.exists(data_path):
        try:
            os.makedirs(data_path, exist_ok=True)
        except OSError:
            return get_base_path()

    return data_path

def get_ffmpeg_path() -> Optional[str]:
    """Return the managed external FFmpeg executable path."""
    from utils.bin.manager import get_ffmpeg_path as get_bin_ffmpeg
    return get_bin_ffmpeg()

def validate_url(url: str) -> bool:
    """Validate URLs by allowing any http or https URL supported by yt-dlp."""
    if not url:
        return False
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme in ('http', 'https'), result.netloc])
    except (AttributeError, TypeError, ValueError):
        return False

def is_youtube_url(url: str) -> bool:
    """Return whether the URL is a YouTube URL for YouTube-specific branching."""
    youtube_patterns = YOUTUBE_URL_PATTERNS
    return any(re.search(pattern, url) for pattern in youtube_patterns)

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