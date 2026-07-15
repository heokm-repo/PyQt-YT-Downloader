"""GitHub release fetch helpers for managed binaries."""

from typing import Callable, Optional, Tuple

import requests

from constants import HTTP_API_TIMEOUT_SEC

from utils.logger import log
from utils.url_security import redact_url_for_log


ReleaseInfoParser = Callable[
    [dict],
    Tuple[Optional[str], Optional[str], Optional[str]],
]


def check_latest_github_release(
    api_url: str,
    display_name: str,
    release_info: ReleaseInfoParser,
    missing_asset_message: str,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Fetch and parse the latest GitHub release for one binary."""
    try:
        log.info(
            f"Checking {display_name} latest version from "
            f"{redact_url_for_log(api_url)}"
        )
        response = requests.get(api_url, timeout=HTTP_API_TIMEOUT_SEC)
        response.raise_for_status()

        version, download_url, digest = release_info(response.json())
        if download_url:
            log.info(f"Latest {display_name} version: {version}")
            return version, download_url, digest

        log.warning(missing_asset_message)
        return None, None, None

    except requests.RequestException as e:
        log.error(f"Failed to check {display_name} version: {e}")
        return None, None, None
