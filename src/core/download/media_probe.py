"""Read media stream properties with the managed FFmpeg toolchain."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import subprocess
from typing import Any

from constants import DEFAULT_ENCODING
from utils.logger import log


MEDIA_PROBE_TIMEOUT_SEC = 10

@dataclass(frozen=True)
class MediaProbeResult:
    """Properties of the first audio and video streams in a media file."""

    audio_sample_rate: int | None = None
    audio_bit_rate: int | None = None
    audio_codec: str | None = None
    video_codec: str | None = None
    video_pixel_format: str | None = None


def _creation_flags() -> int:
    return subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def _positive_int(value: Any) -> int | None:
    try:
        normalized = int(float(str(value).strip()))
    except (OverflowError, TypeError, ValueError):
        return None
    return normalized if normalized > 0 else None


def _normalized_codec(value: Any) -> str | None:
    codec = str(value or "").strip().lower()
    return codec or None


def _sibling_ffprobe_path(ffmpeg_path: str) -> str | None:
    ffmpeg = Path(ffmpeg_path)
    executable_suffix = ".exe" if ffmpeg.suffix.lower() == ".exe" else ""
    candidate = ffmpeg.with_name(f"ffprobe{executable_suffix}")
    return str(candidate) if candidate.is_file() else None


def _probe_with_ffprobe(input_path: str, ffprobe_path: str) -> MediaProbeResult | None:
    try:
        completed = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,codec_name,sample_rate,bit_rate,pix_fmt",
                "-of",
                "json",
                input_path,
            ],
            capture_output=True,
            text=True,
            encoding=DEFAULT_ENCODING,
            errors="replace",
            timeout=MEDIA_PROBE_TIMEOUT_SEC,
            creationflags=_creation_flags(),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        log.debug(f"ffprobe media inspection failed: {exc}")
        return None

    if completed.returncode != 0:
        log.debug(f"ffprobe media inspection exited with code {completed.returncode}")
        return None

    try:
        payload = json.loads(completed.stdout or "{}")
    except (json.JSONDecodeError, TypeError) as exc:
        log.debug(f"ffprobe media inspection returned invalid JSON: {exc}")
        return None

    if not isinstance(payload, dict):
        return None
    streams = payload.get("streams")
    if not isinstance(streams, list):
        return None

    audio_sample_rate = None
    audio_bit_rate = None
    audio_codec = None
    video_codec = None
    video_pixel_format = None
    for stream in streams:
        if not isinstance(stream, dict):
            continue
        stream_type = str(stream.get("codec_type") or "").lower()
        if stream_type == "audio":
            if audio_sample_rate is None:
                audio_sample_rate = _positive_int(stream.get("sample_rate"))
            if audio_bit_rate is None:
                audio_bit_rate = _positive_int(stream.get("bit_rate"))
            if audio_codec is None:
                audio_codec = _normalized_codec(stream.get("codec_name"))
        elif stream_type == "video" and video_codec is None:
            video_codec = _normalized_codec(stream.get("codec_name"))
            video_pixel_format = _normalized_codec(stream.get("pix_fmt"))

    return MediaProbeResult(
        audio_sample_rate=audio_sample_rate,
        audio_bit_rate=audio_bit_rate,
        audio_codec=audio_codec,
        video_codec=video_codec,
        video_pixel_format=video_pixel_format,
    )


def probe_media_file(input_path: str, ffmpeg_path: str | None) -> MediaProbeResult:
    """Return stream properties using the required sibling ffprobe executable."""
    if (
        not input_path
        or not os.path.isfile(input_path)
        or not ffmpeg_path
        or not os.path.isfile(ffmpeg_path)
    ):
        return MediaProbeResult()

    ffprobe_path = _sibling_ffprobe_path(ffmpeg_path)
    if not ffprobe_path:
        log.error("Required ffprobe executable was not found")
        return MediaProbeResult()
    return _probe_with_ffprobe(input_path, ffprobe_path) or MediaProbeResult()
