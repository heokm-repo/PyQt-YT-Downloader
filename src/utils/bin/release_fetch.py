"""GitHub release fetch helpers for managed binaries."""

from typing import Callable, Optional, Tuple

import requests

from constants import HTTP_API_TIMEOUT_SEC

from utils.integrity import normalize_sha256_digest
from utils.logger import log
from utils.url_security import redact_url_for_log, redact_urls_in_text


ReleaseInfoParser = Callable[
    [dict],
    Tuple[Optional[str], Optional[str], Optional[str]],
]


class ReleaseCheckError(RuntimeError):
    """Raised when a managed-binary release cannot be checked reliably."""


def _fetch_latest_github_release(
    api_url: str,
    display_name: str,
    release_info: ReleaseInfoParser,
    missing_asset_message: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Fetch one release, preserving failures for strict callers."""
    log.info(
        f"Checking {display_name} latest version from "
        f"{redact_url_for_log(api_url)}"
    )
    try:
        response = requests.get(api_url, timeout=HTTP_API_TIMEOUT_SEC)
        response.raise_for_status()
        version, download_url, digest = release_info(response.json())
    except requests.RequestException as exc:
        raise ReleaseCheckError(
            f"Failed to check {display_name} version: "
            f"{redact_urls_in_text(exc)}"
        ) from exc
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        raise ReleaseCheckError(
            f"Invalid {display_name} release response: {exc}"
        ) from exc

    if not version or not download_url:
        raise ReleaseCheckError(missing_asset_message)

    log.info(f"Latest {display_name} version: {version}")
    return version, download_url, digest


def check_latest_github_release(
    api_url: str,
    display_name: str,
    release_info: ReleaseInfoParser,
    missing_asset_message: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Fetch and parse the latest GitHub release for one binary."""
    try:
        return _fetch_latest_github_release(
            api_url,
            display_name,
            release_info,
            missing_asset_message,
        )
    except ReleaseCheckError as exc:
        log.error(str(exc))
        return None, None, None


def check_latest_github_release_strict(
    api_url: str,
    display_name: str,
    release_info: ReleaseInfoParser,
    missing_asset_message: str,
) -> Tuple[str, str, str]:
    """Fetch a release or raise when its trusted asset metadata is incomplete."""
    version, download_url, digest = _fetch_latest_github_release(
        api_url,
        display_name,
        release_info,
        missing_asset_message,
    )
    if not normalize_sha256_digest(digest):
        raise ReleaseCheckError(
            f"{display_name} release asset is missing a trusted SHA-256 digest"
        )
    return version, download_url, digest
