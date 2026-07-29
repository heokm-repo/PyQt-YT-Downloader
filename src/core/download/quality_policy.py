"""Source selection and encoder quality policies for media downloads."""

import re
from dataclasses import dataclass

from constants import (
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_VIDEO_QUALITY,
    FORMAT_BESTAUDIO,
)
from core.download.audio_source_policy import AudioSourcePolicy

VIDEO_AUDIO_FINALIZATION_FORMATS = frozenset({"mp4", "mkv"})


@dataclass(frozen=True)
class AudioQualityProfile:
    """Map one audio-quality setting to source and final-encoder policies."""

    source_format: str
    source_selector: str
    encoder_quality: str

    def encoder_quality_for(self, target_format: str) -> str | None:
        """Return a lossy encoder quality, omitting it for PCM WAV output."""
        if target_format.lower() == "wav":
            return None
        return self.encoder_quality


def build_audio_quality_profile(value: object) -> AudioQualityProfile:
    """Build the source selector and encoder mapping for an audio setting."""
    quality = str(value or DEFAULT_AUDIO_QUALITY).strip().lower()
    match = re.fullmatch(r"(\d+)\s*k?", quality)
    bitrate = match.group(1) if match else None

    if quality == "worst":
        return AudioQualityProfile(
            source_format=FORMAT_BESTAUDIO,
            source_selector="bestaudio",
            encoder_quality="10",
        )

    if bitrate:
        bitrate_quality = f"{bitrate}k"
        return AudioQualityProfile(
            source_format=FORMAT_BESTAUDIO,
            source_selector="bestaudio",
            encoder_quality=bitrate_quality,
        )

    return AudioQualityProfile(
        source_format=FORMAT_BESTAUDIO,
        source_selector="bestaudio",
        encoder_quality="0",
    )


def requested_lossy_audio_bitrate(value: object) -> str | None:
    """Return the requested final bitrate, or None when native/best is requested."""
    quality = str(value or DEFAULT_AUDIO_QUALITY).strip().lower()
    if quality == "worst":
        return "48k"
    match = re.fullmatch(r"(\d+)\s*k?", quality)
    if not match or int(match.group(1)) <= 0:
        return None
    return f"{match.group(1)}k"


def video_audio_finalization_bitrate(
    target_format: object,
    audio_quality: object,
    normalize_audio: bool,
) -> str | None:
    """Return a bitrate for the app-owned video audio-only encoding pass."""
    if normalize_audio:
        return None
    normalized_format = str(target_format or "").strip().lower()
    if (
        normalized_format != "webm"
        and normalized_format not in VIDEO_AUDIO_FINALIZATION_FORMATS
    ):
        return None
    return requested_lossy_audio_bitrate(audio_quality)


def requires_video_quality_finalization(
    target_format: object,
    audio_quality: object,
    normalize_audio: bool,
) -> bool:
    """Return whether the app must own the exact-path final media pass."""
    if normalize_audio:
        return False
    normalized_format = str(target_format or "").strip().lower()
    if normalized_format == "webm":
        return True
    if normalized_format not in VIDEO_AUDIO_FINALIZATION_FORMATS:
        return False
    return requested_lossy_audio_bitrate(audio_quality) is not None


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
