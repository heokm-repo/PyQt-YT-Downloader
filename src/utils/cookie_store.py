"""Cookie file storage helpers shared by GUI and downloader code."""

import os

from utils.utils import get_user_data_path

COOKIE_FILENAME = "cookies.txt"


def get_cookie_file_path() -> str:
    """Return the persisted browser cookie file path."""
    return os.path.join(get_user_data_path(), COOKIE_FILENAME)


def cookie_file_exists() -> bool:
    """Return whether the persisted browser cookie file exists."""
    return os.path.exists(get_cookie_file_path())