"""Format combo-box option planning for the settings dialog."""

from dataclasses import dataclass
from typing import Iterable, List

from constants import AUDIO_FORMATS, DEFAULT_FORMAT, FORMAT_OPTIONS, VIDEO_FORMATS

COMPATIBILITY_FORMATS = frozenset({"mp4", "mp3"})


@dataclass(frozen=True)
class FormatComboEntry:
    label: str
    is_header: bool = False


@dataclass(frozen=True)
class FormatQualityControlState:
    video_quality_enabled: bool
    audio_quality_enabled: bool


def build_format_combo_entries(
    video_header: str,
    audio_header: str,
    video_formats: Iterable[str] = VIDEO_FORMATS,
    audio_formats: Iterable[str] = AUDIO_FORMATS,
) -> List[FormatComboEntry]:
    """Return ordered entries for the format combo box."""
    return [
        FormatComboEntry(video_header, is_header=True),
        *[FormatComboEntry(fmt) for fmt in video_formats],
        FormatComboEntry(audio_header, is_header=True),
        *[FormatComboEntry(fmt) for fmt in audio_formats],
    ]


def normalize_format_selection(current_format: str, default_format: str = DEFAULT_FORMAT) -> str:
    """Return a selectable format value, falling back to the default."""
    if current_format in FORMAT_OPTIONS:
        return current_format
    return default_format


def quality_control_state_for_format(
    selected_format: str,
) -> FormatQualityControlState:
    """Return which quality controls have meaning for the selected format."""
    normalized_format = normalize_format_selection(
        str(selected_format or "").strip().lower()
    )
    return FormatQualityControlState(
        video_quality_enabled=normalized_format in VIDEO_FORMATS,
        audio_quality_enabled=normalized_format != "wav",
    )


def normalized_compatibility_format(selected_format: str) -> str:
    """Keep MP4/MP3 selections and use MP4 for incompatible formats."""
    normalized = str(selected_format or "").strip().lower()
    return normalized if normalized in COMPATIBILITY_FORMATS else "mp4"
