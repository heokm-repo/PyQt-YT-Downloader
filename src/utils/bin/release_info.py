"""Parse release metadata for managed binary downloads."""

from typing import Any, Optional, Tuple


def normalize_release_tag(tag: Any) -> str:
    """Normalize GitHub release tags such as v2024.01.30."""
    return str(tag or "").lstrip("v")


def release_version_from_published_or_tag(data: dict[str, Any]) -> str:
    """Use published_at as a date version, falling back to tag_name."""
    published_at = data.get("published_at", "")
    if published_at:
        return str(published_at)[:10].replace("-", ".")
    return normalize_release_tag(data.get("tag_name", ""))


def find_asset_download_url(
    data: dict[str, Any],
    *,
    exact_name: Optional[str] = None,
    name_contains: Optional[str] = None,
) -> Optional[str]:
    """Find an asset download URL by exact name or substring."""
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if exact_name is not None and name != exact_name:
            continue
        if name_contains is not None and name_contains not in name:
            continue
        return asset.get("browser_download_url")
    return None


def ytdlp_release_info(data: dict[str, Any], asset_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Return yt-dlp release version and executable URL from release data."""
    download_url = find_asset_download_url(data, exact_name=asset_name)
    if not download_url:
        return None, None
    return normalize_release_tag(data.get("tag_name", "")), download_url


def ffmpeg_release_info(data: dict[str, Any], asset_name_contains: str) -> Tuple[Optional[str], Optional[str]]:
    """Return FFmpeg release version and zip URL from release data."""
    download_url = find_asset_download_url(data, name_contains=asset_name_contains)
    if not download_url:
        return None, None
    return release_version_from_published_or_tag(data), download_url


def quickjs_release_info(data: dict[str, Any], asset_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Return QuickJS release version and executable URL from release data."""
    download_url = find_asset_download_url(data, exact_name=asset_name)
    if not download_url:
        return None, None
    return normalize_release_tag(data.get("tag_name", "")), download_url