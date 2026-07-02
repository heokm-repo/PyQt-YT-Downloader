"""Build display values for task progress updates."""

import re
from dataclasses import dataclass
from typing import Any, Mapping

from locales.strings import STR
from utils.utils import format_bytes


ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")


@dataclass(frozen=True)
class TaskProgressDisplay:
    percent_text: str
    progress_value: int | None
    size_text: str
    status_text: str


def strip_ansi(value: Any) -> str:
    """Return a string with terminal ANSI escape sequences removed."""
    return ANSI_ESCAPE_RE.sub("", str(value)).strip()


def parse_percent_value(percent_text: str) -> int | None:
    """Return a progress-bar integer value, or None when text is not numeric."""
    try:
        return int(float(percent_text.rstrip("%")))
    except ValueError:
        return None


def build_task_progress_display(progress: Mapping[str, Any]) -> TaskProgressDisplay:
    """Create user-facing display values from a yt-dlp progress dictionary."""
    percent_text = strip_ansi(progress.get("_percent_str") or "0%")
    speed = strip_ansi(progress.get("_speed_str") or "")

    downloaded = format_bytes(progress.get("downloaded_bytes", 0))
    total = format_bytes(progress.get("total_bytes") or progress.get("total_bytes_estimate", 0))

    if progress.get("status", "") == "postprocessing":
        status_text = STR.STATUS_CONVERTING
    elif speed:
        status_text = STR.STATUS_DOWNLOADING_SPEED.format(speed=speed)
    else:
        status_text = STR.STATUS_DOWNLOADING_DOTS

    return TaskProgressDisplay(
        percent_text=percent_text,
        progress_value=parse_percent_value(percent_text),
        size_text=f"{downloaded} / {total}",
        status_text=status_text,
    )