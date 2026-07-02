"""Scheduler-related calculations derived from UI settings."""

from typing import Any, Mapping

from constants import DEFAULT_MAX_DOWNLOADS, KEY_MAX_DOWNLOADS, KEY_USE_ACCELERATION


def target_worker_count(settings: Mapping[str, Any]) -> int:
    """Return the scheduler worker count implied by current settings."""
    if settings.get(KEY_USE_ACCELERATION, False):
        return 1
    return int(settings.get(KEY_MAX_DOWNLOADS, DEFAULT_MAX_DOWNLOADS))


def should_adjust_worker_count(old_settings: Mapping[str, Any], new_settings: Mapping[str, Any]) -> bool:
    """Return whether scheduler worker count should be recalculated."""
    return target_worker_count(old_settings) != target_worker_count(new_settings)
