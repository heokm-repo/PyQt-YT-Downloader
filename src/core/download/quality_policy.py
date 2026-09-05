"""Source selection and encoder quality policies for media downloads."""

import re

from constants import (
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_VIDEO_QUALITY,
)
from core.download.audio_source_policy import AudioSourcePolicy


def requested_lossy_audio_bitrate(value: object) -> str | None:
    """Return the requested final bitrate, or None when native/best is requested."""
    quality = str(value or DEFAULT_AUDIO_QUALITY).strip().lower()
    if quality == "worst":
        return "48k"
    match = re.fullmatch(r"(\d+)\s*k?", quality)
    if not match or int(match.group(1)) <= 0:
        return None
    return f"{match.group(1)}k"


def build_video_source_selector(
    video_quality: object,
    audio_policy: AudioSourcePolicy,
) -> tuple[str, str | None]:
    """Build video choices while always preferring the best available source audio."""
    quality = str(video_quality or DEFAULT_VIDEO_QUALITY).strip().lower()

    if quality in ("best", "worst"):
        video_selector = f"{quality}video"
        combined_fallback = quality
        format_sort = None
    else:
        match = re.fullmatch(r"(\d+)\s*p?", quality)
        if match:
            short_edge = match.group(1)
            video_selector = "bestvideo"
            combined_fallback = "best"
            format_sort = f"res:{short_edge}"
        else:
            return build_video_source_selector(DEFAULT_VIDEO_QUALITY, audio_policy)

    selectors = [f"{video_selector}+{audio_policy.primary}"]
    if audio_policy.fallback != audio_policy.primary:
        selectors.append(f"{video_selector}+{audio_policy.fallback}")
    selectors.append(combined_fallback)
    selector = "/".join(selectors)
    return selector, format_sort
