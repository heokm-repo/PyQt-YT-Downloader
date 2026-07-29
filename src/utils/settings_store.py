"""Settings persistence and download folder normalization."""
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from constants import (
    DEFAULT_ACCELERATION,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_FORMAT,
    DEFAULT_MAX_DOWNLOADS,
    DEFAULT_NORMALIZE,
    DEFAULT_UNIVERSAL_COMPATIBILITY,
    DEFAULT_VIDEO_QUALITY,
    DOWNLOAD_FOLDER_NAME,
    DOWNLOAD_FOLDER_WRITE_TEST_PREFIX,
    ERR_DOWNLOAD_FOLDER_EMPTY,
    ERR_DOWNLOAD_FOLDER_NOT_DIRECTORY,
    ERR_DOWNLOAD_FOLDER_PROTECTED,
    FALLBACK_DOWNLOAD_FOLDER_NAME,
    LEGACY_SAVE_PATH_KEY,
    SETTINGS_FILENAME,
    USER_DOWNLOADS_DIR_NAME,
    WINDOWS_PROTECTED_DEFAULT_FOLDERS,
    WINDOWS_PROTECTED_FOLDER_ENV_VARS,
    WINDOWS_SYSTEM_DRIVE_ENV_VAR,
    WINDOWS_SYSTEM_DRIVE_FALLBACK,
    KEY_AUDIO_QUALITY,
    KEY_DOWNLOAD_FOLDER,
    KEY_FORMAT,
    KEY_LANGUAGE,
    KEY_MAX_DOWNLOADS,
    KEY_NORMALIZE_AUDIO,
    KEY_USE_ACCELERATION,
    KEY_UNIVERSAL_COMPATIBILITY,
    KEY_VIDEO_QUALITY,
)
from locales import DEFAULT_LANGUAGE
from utils.logger import log
from utils.utils import get_base_path, get_user_data_path


@dataclass(frozen=True)
class DownloadFolderFallbackNotice:
    original_path: str
    fallback_path: str
    reason: str


_pending_download_folder_notice: DownloadFolderFallbackNotice | None = None


def default_download_folder() -> str:
    return os.path.join(get_base_path(), DOWNLOAD_FOLDER_NAME)


def fallback_download_folder() -> str:
    return os.path.join(str(Path.home()), USER_DOWNLOADS_DIR_NAME, FALLBACK_DOWNLOAD_FOLDER_NAME)


def default_settings() -> dict[str, Any]:
    return {
        KEY_DOWNLOAD_FOLDER: default_download_folder(),
        KEY_VIDEO_QUALITY: DEFAULT_VIDEO_QUALITY,
        KEY_AUDIO_QUALITY: DEFAULT_AUDIO_QUALITY,
        KEY_FORMAT: DEFAULT_FORMAT,
        KEY_MAX_DOWNLOADS: DEFAULT_MAX_DOWNLOADS,
        KEY_NORMALIZE_AUDIO: DEFAULT_NORMALIZE,
        KEY_USE_ACCELERATION: DEFAULT_ACCELERATION,
        KEY_UNIVERSAL_COMPATIBILITY: DEFAULT_UNIVERSAL_COMPATIBILITY,
        KEY_LANGUAGE: DEFAULT_LANGUAGE,
    }


def settings_file_path() -> str:
    return os.path.join(get_user_data_path(), SETTINGS_FILENAME)


def consume_download_folder_fallback_notice() -> DownloadFolderFallbackNotice | None:
    global _pending_download_folder_notice
    notice = _pending_download_folder_notice
    _pending_download_folder_notice = None
    return notice


def get_download_folder(settings: dict[str, Any]) -> str:
    folder = settings.get(KEY_DOWNLOAD_FOLDER)
    if not folder and settings.get(LEGACY_SAVE_PATH_KEY):
        folder = settings[LEGACY_SAVE_PATH_KEY]
        settings[KEY_DOWNLOAD_FOLDER] = folder
        settings.pop(LEGACY_SAVE_PATH_KEY, None)
    if not folder:
        folder = default_download_folder()
        settings[KEY_DOWNLOAD_FOLDER] = folder
    return folder


def load_settings() -> dict[str, Any]:
    settings = default_settings()
    path = settings_file_path()
    migrated_legacy_path = False

    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)
            if isinstance(loaded_settings, dict):
                if KEY_DOWNLOAD_FOLDER not in loaded_settings and loaded_settings.get(LEGACY_SAVE_PATH_KEY):
                    loaded_settings[KEY_DOWNLOAD_FOLDER] = loaded_settings[LEGACY_SAVE_PATH_KEY]
                    migrated_legacy_path = True
                settings.update(loaded_settings)
    except (OSError, json.JSONDecodeError, TypeError) as e:
        log.error(f"Settings load failed: {e}", exc_info=True)

    changed = _normalize_download_folder(settings)
    had_legacy_path = LEGACY_SAVE_PATH_KEY in settings
    settings.pop(LEGACY_SAVE_PATH_KEY, None)
    if changed or migrated_legacy_path or had_legacy_path:
        _write_settings_file(settings)

    return settings


def save_settings(settings: dict[str, Any]) -> dict[str, Any]:
    _normalize_download_folder(settings)
    settings.pop(LEGACY_SAVE_PATH_KEY, None)
    _write_settings_file(settings)
    return settings


def _write_settings_file(settings: dict[str, Any]) -> None:
    try:
        path = settings_file_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except (OSError, TypeError) as e:
        log.error(f"Settings save failed: {e}", exc_info=True)


def _normalize_download_folder(settings: dict[str, Any]) -> bool:
    original_path = get_download_folder(settings)
    ok, reason = _ensure_writable_folder(original_path)
    if ok:
        return False

    fallback_path = fallback_download_folder()
    fallback_ok, fallback_reason = _ensure_writable_folder(fallback_path)
    settings[KEY_DOWNLOAD_FOLDER] = fallback_path
    _set_download_folder_notice(
        original_path,
        fallback_path,
        fallback_reason if not fallback_ok else reason,
    )
    return True


def _set_download_folder_notice(original_path: str, fallback_path: str, reason: str) -> None:
    global _pending_download_folder_notice
    _pending_download_folder_notice = DownloadFolderFallbackNotice(
        original_path=original_path,
        fallback_path=fallback_path,
        reason=reason,
    )
    log.warning(
        "Download folder changed to fallback: %s -> %s (%s)",
        original_path,
        fallback_path,
        reason,
    )


def _protected_windows_folder_reason(path: str) -> str | None:
    if os.name != 'nt':
        return None

    protected_roots = _windows_protected_roots()
    if not protected_roots:
        return None

    normalized_path = os.path.normcase(os.path.normpath(os.path.abspath(path)))
    for root in protected_roots:
        if normalized_path == root or normalized_path.startswith(root + os.sep):
            return ERR_DOWNLOAD_FOLDER_PROTECTED

    return None


def _windows_protected_roots() -> set[str]:
    roots = set()
    for key in WINDOWS_PROTECTED_FOLDER_ENV_VARS:
        value = os.environ.get(key)
        if value:
            roots.add(os.path.normcase(os.path.normpath(os.path.abspath(value))))

    system_drive = os.environ.get(WINDOWS_SYSTEM_DRIVE_ENV_VAR, WINDOWS_SYSTEM_DRIVE_FALLBACK)
    for folder_name in WINDOWS_PROTECTED_DEFAULT_FOLDERS:
        roots.add(os.path.normcase(os.path.normpath(os.path.abspath(os.path.join(system_drive + os.sep, folder_name)))))
    return roots


def _ensure_writable_folder(path: str) -> tuple[bool, str]:
    if not path:
        return False, ERR_DOWNLOAD_FOLDER_EMPTY

    protected_reason = _protected_windows_folder_reason(path)
    if protected_reason:
        return False, protected_reason

    try:
        os.makedirs(path, exist_ok=True)
        if not os.path.isdir(path):
            return False, ERR_DOWNLOAD_FOLDER_NOT_DIRECTORY

        fd, temp_path = tempfile.mkstemp(prefix=DOWNLOAD_FOLDER_WRITE_TEST_PREFIX, dir=path)
        os.close(fd)
        os.remove(temp_path)
        return True, ''
    except OSError as e:
        return False, str(e)
