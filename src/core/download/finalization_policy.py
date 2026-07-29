"""Build one media-finalization policy from download settings and probe data."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from constants import (
    AUDIO_CHANNELS,
    AUDIO_FORMATS,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_FORMAT,
    KEY_UNIVERSAL_COMPATIBILITY,
    LOUDNORM_FILTER,
)
from core.download.media_probe import MediaProbeResult
from core.download.audio_encoding_policy import build_audio_codec_args
from core.download.webm_encoding import is_webm_video_codec


@dataclass(frozen=True)
class FinalizationPlan:
    target_format: str
    audio_only: bool
    video_args: tuple[str, ...]
    audio_args: tuple[str, ...]
    audio_filter: str | None
    audio_channels: int
    requires_ffmpeg: bool
    compatibility: bool


def target_output_format(settings: Mapping[str, Any]) -> str:
    """Return the effective final extension after compatibility coercion."""
    target_format = str(settings.get("format", DEFAULT_FORMAT)).strip().lower()
    if (
        settings.get(KEY_UNIVERSAL_COMPATIBILITY)
        and target_format not in {"mp4", "mp3"}
    ):
        return "mp4"
    return target_format


def build_finalization_plan(
    settings: Mapping[str, Any],
    probe: MediaProbeResult,
    source_path: object = None,
) -> FinalizationPlan:
    """Return selective copy/encode decisions for a single FFmpeg pass."""
    target_format = target_output_format(settings)
    compatibility = bool(settings.get(KEY_UNIVERSAL_COMPATIBILITY))
    normalize = bool(settings.get("normalize_audio"))
    audio_only = target_format in AUDIO_FORMATS
    quality = (
        DEFAULT_AUDIO_QUALITY
        if target_format == "wav"
        else settings.get("audio_quality", DEFAULT_AUDIO_QUALITY)
    )

    if audio_only:
        video_args: tuple[str, ...] = ()
    elif target_format == "webm":
        video_args = (
            ("-c:v", "copy")
            if is_webm_video_codec(probe.video_codec)
            else (
                "-c:v", "libvpx-vp9", "-crf", "30", "-b:v", "0",
                "-deadline", "good", "-cpu-used", "2", "-row-mt", "1",
            )
        )
    elif compatibility:
        video_args = (
            ("-c:v", "copy")
            if probe.video_codec == "h264"
            and probe.video_pixel_format == "yuv420p"
            else (
                "-c:v", "libx264", "-preset", "medium", "-crf", "18",
                "-pix_fmt", "yuv420p",
            )
        )
    else:
        video_args = ("-c:v", "copy")

    audio_args = build_audio_codec_args(
        target_format,
        quality,
        settings,
        probe,
        normalize,
        compatibility,
    )
    audio_filter = None
    if normalize:
        if probe.audio_sample_rate is None:
            raise ValueError("Input audio sample rate could not be determined")
        audio_filter = f"{LOUDNORM_FILTER},aresample={probe.audio_sample_rate}"

    video_requires_encode = (
        not audio_only and video_args != ("-c:v", "copy")
    )
    source_extension = (
        Path(str(source_path)).suffix.lower()
        if source_path
        else ""
    )
    m4a_requires_remux = target_format == "m4a" and (
        probe.video_codec is not None
        or bool(source_extension and source_extension != ".m4a")
    )
    webm_requires_remux = (
        target_format == "webm"
        and bool(source_extension and source_extension != ".webm")
    )
    requires_ffmpeg = (
        target_format in {"mp3", "wav"}
        or normalize
        or video_requires_encode
        or m4a_requires_remux
        or webm_requires_remux
        or audio_args != ("-c:a", "copy")
    )
    return FinalizationPlan(
        target_format=target_format,
        audio_only=audio_only,
        video_args=video_args,
        audio_args=audio_args,
        audio_filter=audio_filter,
        audio_channels=int(settings.get("audio_channels", AUDIO_CHANNELS)),
        requires_ffmpeg=requires_ffmpeg,
        compatibility=compatibility,
    )
