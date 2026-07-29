"""Choose copy or codec-specific audio encoding for final media output."""

from __future__ import annotations

import re
from typing import Any, Mapping

from constants import DEFAULT_AUDIO_QUALITY
from core.download.media_probe import MediaProbeResult
from core.download.webm_encoding import is_webm_audio_codec


def _quality_bitrate(value: object) -> str | None:
    quality = str(value or DEFAULT_AUDIO_QUALITY).strip().lower()
    if quality == "worst":
        return "48k"
    match = re.fullmatch(r"(\d+)\s*k?", quality)
    return f"{match.group(1)}k" if match and int(match.group(1)) > 0 else None


def _selected_bitrate(settings: Mapping[str, Any], probe: MediaProbeResult) -> int | None:
    # FFprobe reports the encoded stream bitrate. yt-dlp's abr can include
    # container overhead (for example, 128k AAC may be reported as ~129.5k),
    # so only use yt-dlp metadata when the stream itself has no bitrate.
    for value in (
        probe.audio_bit_rate,
        settings.get("_selected_audio_bitrate"),
    ):
        try:
            normalized = int(value)
        except (TypeError, ValueError):
            continue
        if normalized > 0:
            return normalized
    return None


def _within_requested_cap(
    quality: object,
    settings: Mapping[str, Any],
    probe: MediaProbeResult,
) -> bool:
    requested = _quality_bitrate(quality)
    if requested is None:
        return True
    selected = _selected_bitrate(settings, probe)
    if selected is None:
        return False
    return selected <= int(requested[:-1]) * 1000


def _mkv_encoder(codec: str | None) -> str:
    if codec in {"opus", "vorbis"}:
        return "libopus"
    if codec == "mp3":
        return "libmp3lame"
    return "aac"


def build_audio_codec_args(
    target_format: str,
    quality: object,
    settings: Mapping[str, Any],
    probe: MediaProbeResult,
    normalize: bool,
    compatibility: bool,
) -> tuple[str, ...]:
    """Return audio codec arguments, copying compatible streams under the cap."""
    normalized_quality = str(quality or DEFAULT_AUDIO_QUALITY).strip().lower()
    bitrate = _quality_bitrate(normalized_quality)

    if target_format == "mp3":
        if normalized_quality == "best":
            return ("-c:a", "libmp3lame", "-q:a", "0")
        if normalized_quality == "worst":
            return ("-c:a", "libmp3lame", "-q:a", "9")
        return ("-c:a", "libmp3lame", "-b:a", bitrate or "192k")
    if target_format == "wav":
        return ("-c:a", "pcm_s16le")

    if target_format in {"m4a", "mp4"} or compatibility:
        compatible = (
            probe.audio_codec == "aac"
            if target_format == "m4a"
            else probe.audio_codec in {None, "aac"}
        )
        if (
            not normalize
            and compatible
            and (
                normalized_quality == "worst"
                or _within_requested_cap(normalized_quality, settings, probe)
            )
        ):
            return ("-c:a", "copy")
        return ("-c:a", "aac", "-b:a", bitrate or "192k")

    if target_format == "webm":
        compatible = probe.audio_codec is None or is_webm_audio_codec(probe.audio_codec)
        if (
            not normalize
            and compatible
            and (
                normalized_quality == "worst"
                or _within_requested_cap(normalized_quality, settings, probe)
            )
        ):
            return ("-c:a", "copy")
        return ("-c:a", "libopus", "-b:a", bitrate or "160k")

    if target_format == "mkv":
        if (
            not normalize
            and (
                normalized_quality == "worst"
                or _within_requested_cap(normalized_quality, settings, probe)
            )
        ):
            return ("-c:a", "copy")
        return (
            "-c:a",
            _mkv_encoder(probe.audio_codec),
            "-b:a",
            bitrate or "192k",
        )

    return ("-c:a", "copy")
