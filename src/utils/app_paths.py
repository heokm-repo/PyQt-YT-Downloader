"""Application paths without logging, binary-manager or GUI dependencies."""

import os
import sys

from constants import APPDATA_DIR_NAME, APPDATA_ENV_VAR


def get_base_path() -> str:
    """Return the source or frozen executable directory."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_user_data_path() -> str:
    """Use AppData, retaining the existing source/executable fallback."""
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
