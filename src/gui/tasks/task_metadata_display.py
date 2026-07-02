"""Build display values for task metadata shown in task widgets."""

from dataclasses import dataclass
from typing import Any, Mapping

from utils.utils import format_bytes


DEFAULT_TITLE = "(제목 없음)"
DEFAULT_UPLOADER = "Unknown"


@dataclass(frozen=True)
class TaskMetadataDisplay:
    title_text: str
    uploader_text: str
    file_size_text: str | None
    thumbnail_url: str | None


def format_task_title(text: Any, settings: Mapping[str, Any] | None) -> str:
    """Return the task title with the selected download format prefix."""
    task_format = (settings or {}).get("format", "mp4").upper()
    return f"[{task_format}] {text}"


def build_task_metadata_display(
    metadata: Mapping[str, Any], settings: Mapping[str, Any] | None
) -> TaskMetadataDisplay:
    """Create user-facing label values from fetched or restored metadata."""
    file_size_text = None
    if "file_size" in metadata:
        file_size_text = format_bytes(metadata["file_size"])

    return TaskMetadataDisplay(
        title_text=format_task_title(metadata.get("title", DEFAULT_TITLE), settings),
        uploader_text=metadata.get("uploader", DEFAULT_UPLOADER),
        file_size_text=file_size_text,
        thumbnail_url=metadata.get("thumbnail"),
    )