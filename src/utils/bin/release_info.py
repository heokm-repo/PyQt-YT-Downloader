"""Parse release metadata for managed binary downloads."""

from typing import Any, Optional, Tuple


ReleaseInfo = Tuple[Optional[str], Optional[str], Optional[str]]


def normalize_release_tag(tag: Any) -> str:
    """Normalize GitHub release tags such as v2024.01.30."""
    return str(tag or "").lstrip("v")


def release_version_from_published_or_tag(data: dict[str, Any]) -> str:
    """Use published_at as a date version, falling back to tag_name."""
    published_at = data.get("published_at", "")
    if published_at:
        return str(published_at)[:10].replace("-", ".")
    return normalize_release_tag(data.get("tag_name", ""))


def find_release_asset(
    data: dict[str, Any],
    *,
    exact_name: Optional[str] = None,
    name_contains: Optional[str] = None,
) -> dict[str, Any] | None:
    """Find a release asset dictionary by exact name or substring."""
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if exact_name is not None and name != exact_name:
            continue
        if name_contains is not None and name_contains not in name:
            continue
        return asset
    return None


def release_asset_info(
    data: dict[str, Any],
    *,
    exact_name: Optional[str] = None,
    name_contains: Optional[str] = None,
) -> tuple[Optional[str], Optional[str]]:
    """Return the selected asset's download URL and GitHub SHA-256 digest."""
    asset = find_release_asset(
        data,
        exact_name=exact_name,
        name_contains=name_contains,
    )
    if not asset:
        return None, None
    return asset.get("browser_download_url"), asset.get("digest")


def ytdlp_release_info(data: dict[str, Any], asset_name: str) -> ReleaseInfo:
    """Return yt-dlp release version, executable URL, and SHA-256 digest."""
    download_url, digest = release_asset_info(data, exact_name=asset_name)
    if not download_url:
        return None, None, None
    return normalize_release_tag(data.get("tag_name", "")), download_url, digest


def ffmpeg_release_info(data: dict[str, Any], asset_name_contains: str) -> ReleaseInfo:
    """Return FFmpeg release version, ZIP URL, and SHA-256 digest."""
    download_url, digest = release_asset_info(data, exact_name=asset_name_contains)
    if not download_url:
        download_url, digest = release_asset_info(
            data,
            name_contains=asset_name_contains,
        )
    if not download_url:
        return None, None, None
    return release_version_from_published_or_tag(data), download_url, digest


def quickjs_release_info(data: dict[str, Any], asset_name: str) -> ReleaseInfo:
    """Return QuickJS release version, executable URL, and SHA-256 digest."""
    download_url, digest = release_asset_info(data, exact_name=asset_name)
    if not download_url:
        return None, None, None
    return normalize_release_tag(data.get("tag_name", "")), download_url, digest
