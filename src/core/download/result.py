"""Result types for completed download executions."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a download, including yt-dlp's exact final output path."""

    success: bool
    message: str
    final_path: str = ""

    def as_legacy_tuple(self) -> Tuple[bool, str]:
        """Return the historical ``(success, message)`` API shape."""
        return self.success, self.message
