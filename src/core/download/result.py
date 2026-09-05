"""Result types for completed download executions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    """Outcome of a download, including yt-dlp's exact final output path."""

    success: bool
    message: str
    final_path: str = ""
