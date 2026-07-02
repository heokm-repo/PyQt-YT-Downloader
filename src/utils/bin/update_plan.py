"""Planning helpers for binary update/download workflows."""

from datetime import datetime, timedelta
from typing import Any, Callable, Mapping, Optional, Sequence

MANAGED_UPDATE_BINARIES = ("yt-dlp", "ffmpeg")


def initial_update_results(binary_names: Sequence[str] = MANAGED_UPDATE_BINARIES) -> dict[str, bool]:
    """Return the initial update result map for managed binaries."""
    return {binary_name: False for binary_name in binary_names}


def selected_update_binaries(
    updates_to_apply: Optional[Mapping[str, Any]],
    default_binaries: Sequence[str] = MANAGED_UPDATE_BINARIES,
) -> list[str]:
    """Return binaries to check/update from an optional update selection."""
    if updates_to_apply is None:
        return list(default_binaries)
    return list(updates_to_apply.keys())


def scoped_progress_callback(
    binary_name: str,
    progress_callback: Optional[Callable[[str, int, int], None]],
) -> Optional[Callable[[int, int], None]]:
    """Wrap a shared binary progress callback for one binary name."""
    if progress_callback is None:
        return None

    def relay(downloaded: int, total: int) -> None:
        progress_callback(binary_name, downloaded, total)

    return relay


def needs_update_from_versions(current_version: Any, latest_version: Any) -> bool:
    """Return whether a binary should update from current/latest versions."""
    if not current_version:
        return True
    if not latest_version:
        return False
    return current_version != latest_version


def update_entry(current_version: Any, latest_version: Any) -> Optional[dict[str, str]]:
    """Return an update entry when both versions exist and differ."""
    if not current_version or not latest_version or current_version == latest_version:
        return None
    return {"current": str(current_version), "latest": str(latest_version)}


def collect_available_updates(
    current_versions: Mapping[str, Any],
    latest_versions: Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    """Build update entries from current and latest version maps."""
    updates: dict[str, dict[str, str]] = {}
    for binary_name, latest_version in latest_versions.items():
        entry = update_entry(current_versions.get(binary_name), latest_version)
        if entry:
            updates[binary_name] = entry
    return updates


def should_check_after(
    last_check: Any,
    interval_hours: int,
    now: Optional[datetime] = None,
) -> bool:
    """Return whether enough time elapsed since the previous update check."""
    if not last_check:
        return True

    try:
        last_checked_at = datetime.fromisoformat(last_check)
        reference_time = now or datetime.now()
        return reference_time - last_checked_at > timedelta(hours=interval_hours)
    except (TypeError, ValueError):
        return True
