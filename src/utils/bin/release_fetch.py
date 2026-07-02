"""GitHub release fetch helpers for managed binaries."""

from typing import Callable, Optional, Tuple

import requests

from utils.logger import log


ReleaseInfoParser = Callable[[dict], Tuple[Optional[str], Optional[str]]]


def check_latest_github_release(
    api_url: str,
    display_name: str,
    release_info: ReleaseInfoParser,
    missing_asset_message: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Fetch and parse the latest GitHub release for one binary."""
    try:
        log.info(f"Checking {display_name} latest version from {api_url}")
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()

        version, download_url = release_info(response.json())
        if download_url:
            log.info(f"Latest {display_name} version: {version}, URL: {download_url}")
            return version, download_url

        log.warning(missing_asset_message)
        return None, None

    except requests.RequestException as e:
        log.error(f"Failed to check {display_name} version: {e}")
        return None, None