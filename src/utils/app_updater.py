"""Application self-update helpers using the GitHub Releases API."""

import os
import subprocess
import sys

import requests
from packaging import version
from packaging.version import InvalidVersion

from constants import (
    APP_RELEASE_API_URL,
    APP_UPDATE_ASSET_EXTENSION,
    APP_UPDATE_ASSET_PREFIX,
    APP_UPDATE_TEMP_ENV_VARS,
    APP_UPDATE_TEMP_FALLBACK_DIR,
    APP_VERSION,
    HTTP_API_TIMEOUT_SEC,
    INNO_SETUP_INSTALL_ARGS,
    UPDATE_TEMP_FILENAME,
)
from utils.download_progress import ProgressReporter
from utils.download_stream import DownloadCancelled, transfer_to_file
from utils.integrity import normalize_sha256_digest, verify_sha256
from utils.logger import log
from utils.url_security import redact_urls_in_text
from locales.strings import STR


GITHUB_API_URL = APP_RELEASE_API_URL


class AppUpdateCheckError(RuntimeError):
    """Raised when an application update check cannot complete reliably."""


def update_temp_dir() -> str:
    """Return the temp directory used for downloaded app updates."""
    for env_var in APP_UPDATE_TEMP_ENV_VARS:
        temp_dir = os.environ.get(env_var)
        if temp_dir:
            return temp_dir
    return APP_UPDATE_TEMP_FALLBACK_DIR


def _select_update_asset(release_data: dict) -> dict | None:
    """Prefer the Setup executable, then fall back to another EXE asset."""
    assets = release_data.get("assets", [])
    for asset in assets:
        name = str(asset.get("name", ""))
        if (
            name.lower().startswith(APP_UPDATE_ASSET_PREFIX)
            and name.lower().endswith(APP_UPDATE_ASSET_EXTENSION)
        ):
            return asset
    for asset in assets:
        name = str(asset.get("name", ""))
        if name.lower().endswith(APP_UPDATE_ASSET_EXTENSION):
            return asset
    return None


def _check_for_updates():
    """Return update information while preserving errors for strict callers."""
    log.info("Checking for app updates")
    response = requests.get(GITHUB_API_URL, timeout=HTTP_API_TIMEOUT_SEC)
    try:
        response.raise_for_status()
        release_data = response.json()
    finally:
        response.close()
    if not isinstance(release_data, dict):
        raise AppUpdateCheckError(STR.ERR_RELEASE_INVALID_FMT.format(name="GitHub"))

    latest_version = str(release_data.get("tag_name", "")).lstrip("v")
    if not latest_version:
        raise AppUpdateCheckError(STR.ERR_RELEASE_VERSION_FMT.format(name="GitHub"))

    current_version = APP_VERSION.lstrip("v")
    log.info(f"Current version: {current_version}, latest version: {latest_version}")
    if version.parse(latest_version) <= version.parse(current_version):
        log.info("Application is already up to date")
        return False, None, None, None

    asset = _select_update_asset(release_data)
    if not asset:
        raise AppUpdateCheckError(
            STR.ERR_RELEASE_ASSET_FMT.format(name="GitHub")
        )

    download_url = asset.get("browser_download_url")
    expected_digest = asset.get("digest")
    if not download_url or not normalize_sha256_digest(expected_digest):
        raise AppUpdateCheckError(
            STR.ERR_RELEASE_TRUST_FMT.format(name="GitHub")
        )

    log.info(f"App update available: {latest_version}")
    return True, latest_version, download_url, expected_digest


def _app_update_check_error(exc: Exception) -> AppUpdateCheckError:
    """Normalize low-level update failures for logs and user-visible status."""
    if isinstance(exc, AppUpdateCheckError):
        return exc
    return AppUpdateCheckError(
        STR.ERR_RELEASE_CHECK_FMT.format(name="GitHub", error=redact_urls_in_text(exc))
    )


def check_for_updates():
    """Return update availability, logging and suppressing check failures."""
    try:
        return _check_for_updates()
    except (
        AppUpdateCheckError,
        InvalidVersion,
        KeyError,
        TypeError,
        ValueError,
        requests.exceptions.RequestException,
    ) as exc:
        error = _app_update_check_error(exc)
        log.error(str(error), exc_info=True)
        return False, None, None, None


def check_for_updates_strict():
    """Return update information or raise a user-visible check failure."""
    try:
        return _check_for_updates()
    except (
        AppUpdateCheckError,
        InvalidVersion,
        KeyError,
        TypeError,
        ValueError,
        requests.exceptions.RequestException,
    ) as exc:
        raise _app_update_check_error(exc) from exc


def _remove_downloaded_update(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as exc:
        log.warning(f"Failed to remove untrusted update file: {exc}")


def download_update(
    download_url, progress_callback=None, expected_digest=None, check_cancel=None,
):
    """Download an installer and return its path only after SHA-256 verification."""
    temp_file_path = None
    try:
        if not normalize_sha256_digest(expected_digest):
            log.error("Missing trusted SHA-256 digest for app update")
            return None

        log.info("Starting app update download")
        temp_file_path = os.path.join(update_temp_dir(), UPDATE_TEMP_FILENAME)

        progress = ProgressReporter(progress_callback)
        result = transfer_to_file(
            download_url, temp_file_path,
            lambda downloaded, total: progress.update(int(downloaded / total * 100)),
            check_cancel,
        )
        if result.total > 0:
            progress.update(int(result.downloaded / result.total * 100), force=True)

        if not verify_sha256(temp_file_path, expected_digest):
            _remove_downloaded_update(temp_file_path)
            return None

        if check_cancel and check_cancel():
            raise DownloadCancelled(started=True)

        log.info(f"App update downloaded and verified: {temp_file_path}")
        return temp_file_path

    except (
        OSError,
        RuntimeError,
        requests.exceptions.RequestException,
        ValueError,
    ) as exc:
        log.error(f"App update download failed: {exc}", exc_info=True)
        _remove_downloaded_update(temp_file_path)
        return None


def apply_update(setup_exe_path, expected_digest=None):
    """Start the verified Inno Setup installer in packaged builds."""
    try:
        if not getattr(sys, "frozen", False):
            log.warning("App updates cannot be applied in a development environment")
            return False
        if not os.path.exists(setup_exe_path):
            log.error(f"Setup file not found: {setup_exe_path}")
            return False
        if not verify_sha256(setup_exe_path, expected_digest):
            log.error("Setup file failed the final SHA-256 check")
            _remove_downloaded_update(setup_exe_path)
            return False

        subprocess.Popen(
            [setup_exe_path, *INNO_SETUP_INSTALL_ARGS],
            creationflags=(
                subprocess.CREATE_NO_WINDOW
                if hasattr(subprocess, "CREATE_NO_WINDOW")
                else 0
            ),
        )
        log.info("Verified setup installer started")
        return True
    except (OSError, subprocess.SubprocessError) as exc:
        log.error(f"Failed to apply app update: {exc}", exc_info=True)
        return False
