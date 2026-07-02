"""Settings dialog rules for download acceleration controls."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MaxDownloadsControlState:
    enabled: bool
    value: Optional[int] = None


def max_downloads_state_for_acceleration(checked: bool) -> MaxDownloadsControlState:
    """Return the max-downloads spinbox state for the acceleration checkbox."""
    if checked:
        return MaxDownloadsControlState(enabled=False, value=1)
    return MaxDownloadsControlState(enabled=True)