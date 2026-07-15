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
    HTTP_DOWNLOAD_CHUNK_SIZE,
    HTTP_DOWNLOAD_TIMEOUT_SEC,
    INNO_SETUP_INSTALL_ARGS,
    UPDATE_TEMP_FILENAME,
)
from utils.integrity import normalize_sha256_digest, verify_sha256
from utils.logger import log


GITHUB_API_URL = APP_RELEASE_API_URL


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


def check_for_updates():
    """Return update availability, version, download URL, and trusted digest."""
    try:
        log.info("Checking for app updates")
        response = requests.get(GITHUB_API_URL, timeout=HTTP_API_TIMEOUT_SEC)
        response.raise_for_status()

        release_data = response.json()
        latest_version = str(release_data.get("tag_name", "")).lstrip("v")
        if not latest_version:
            log.warning("GitHub release did not contain a version")
            return False, None, None, None

        current_version = APP_VERSION.lstrip("v")
        log.info(f"Current version: {current_version}, latest version: {latest_version}")
        if version.parse(latest_version) <= version.parse(current_version):
            log.info("Application is already up to date")
            return False, None, None, None

        asset = _select_update_asset(release_data)
        if not asset:
            log.warning("GitHub release did not contain an installer executable")
            return False, None, None, None

        download_url = asset.get("browser_download_url")
        expected_digest = asset.get("digest")
        if not download_url or not normalize_sha256_digest(expected_digest):
            log.error("App update asset is missing its URL or trusted SHA-256 digest")
            return False, None, None, None

        log.info(f"App update available: {latest_version}")
        return True, latest_version, download_url, expected_digest

    except requests.exceptions.RequestException as exc:
        log.error(f"GitHub API request failed: {exc}", exc_info=True)
    except (InvalidVersion, KeyError, TypeError, ValueError) as exc:
        log.error(f"App update check failed: {exc}", exc_info=True)
    return False, None, None, None


def _remove_downloaded_update(file_path: str | None) -> None:
    if not file_path:
        return
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as exc:
        log.warning(f"Failed to remove untrusted update file: {exc}")


def download_update(download_url, progress_callback=None, expected_digest=None):
    """Download an installer and return its path only after SHA-256 verification."""
    temp_file_path = None
    try:
        if not normalize_sha256_digest(expected_digest):
            log.error("Missing trusted SHA-256 digest for app update")
            return None

        log.info("Starting app update download")
        temp_file_path = os.path.join(update_temp_dir(), UPDATE_TEMP_FILENAME)

        response = requests.get(
            download_url,
            stream=True,
            timeout=HTTP_DOWNLOAD_TIMEOUT_SEC,
        )
        response.raise_for_status()

        total_size = int(response.headers.get("content-length", 0))
        downloaded = 0
        with open(temp_file_path, "wb") as file_handle:
            for chunk in response.iter_content(chunk_size=HTTP_DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                file_handle.write(chunk)
                downloaded += len(chunk)
                if progress_callback and total_size > 0:
                    progress_callback(int((downloaded / total_size) * 100))

        if not verify_sha256(temp_file_path, expected_digest):
            _remove_downloaded_update(temp_file_path)
            return None

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
