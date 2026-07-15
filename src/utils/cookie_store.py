"""Cookie file storage helpers shared by GUI and downloader code."""

import os
import shutil

from constants import WEBENGINE_CACHE_DIR, WEBENGINE_STORAGE_DIR

from utils.utils import get_user_data_path
from utils.logger import log

COOKIE_FILENAME = "cookies.txt"
YOUTUBE_COOKIE_DOMAIN = "youtube.com"


def get_cookie_file_path() -> str:
    """Return the persisted browser cookie file path."""
    return os.path.join(get_user_data_path(), COOKIE_FILENAME)


def cookie_file_exists() -> bool:
    """Return whether the persisted browser cookie file exists."""
    return os.path.exists(get_cookie_file_path())


def delete_cookie_file() -> bool:
    """Delete the exported Netscape cookie file if it exists."""
    cookie_path = get_cookie_file_path()
    try:
        if os.path.exists(cookie_path):
            os.remove(cookie_path)
        return True
    except OSError as exc:
        log.error(f"Failed to delete cookie file: {exc}")
        return False


def delete_webengine_storage() -> bool:
    """Delete legacy WebEngine cache and persistent-storage directories."""
    success = True
    data_path = get_user_data_path()
    for folder in (WEBENGINE_CACHE_DIR, WEBENGINE_STORAGE_DIR):
        path = os.path.join(data_path, folder)
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
        except OSError as exc:
            success = False
            log.warning(f"Failed to delete WebEngine storage {folder}: {exc}")
    return success


def delete_stored_login_data() -> bool:
    """Delete exported cookies and any legacy browser persistence."""
    cookie_deleted = delete_cookie_file()
    webengine_deleted = delete_webengine_storage()
    return cookie_deleted and webengine_deleted


def is_youtube_cookie_domain(domain: str) -> bool:
    """Return whether a cookie domain is youtube.com or one of its subdomains."""
    normalized = str(domain or "").strip().lower().lstrip(".").rstrip(".")
    return (
        normalized == YOUTUBE_COOKIE_DOMAIN
        or normalized.endswith(f".{YOUTUBE_COOKIE_DOMAIN}")
    )
