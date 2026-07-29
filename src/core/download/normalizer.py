"""Format-aware loudness normalization using the managed FFmpeg executable."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Any, Callable, Mapping
from uuid import uuid4

from constants import (
    AUDIO_CHANNELS,
    AUDIO_FORMATS,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_FORMAT,
    FFMPEG_NORMALIZE_TIMEOUT_SEC,
    LOUDNORM_FILTER,
    MSG_PAUSED_BY_USER,
    VIDEO_FORMATS,
)
from core.download.ffmpeg_process import run_ffmpeg_command
from core.download.media_probe import probe_media_file
from core.download.webm_encoding import webm_video_encoding_args
from utils.logger import log
from utils.url_security import redact_urls_in_text


@dataclass(frozen=True)
class NormalizationResult:
    success: bool
    output_path: str
    error: str = ""
    paused: bool = False


def _bitrate_from_quality(quality: Any, *, best: str = "192k") -> str:
    normalized = str(quality or DEFAULT_AUDIO_QUALITY).strip().lower()
    if normalized == "worst":
        return "48k"
    match = re.fullmatch(r"(\d+)\s*k?", normalized)
    if match:
        return f"{match.group(1)}k"
    return best


def _audio_codec_args(target_format: str, audio_quality: Any) -> list[str]:
    if target_format == "mp3":
        normalized = str(audio_quality or DEFAULT_AUDIO_QUALITY).strip().lower()
        if normalized == "best":
            return ["-c:a", "libmp3lame", "-q:a", "0"]
        if normalized == "worst":
            return ["-c:a", "libmp3lame", "-q:a", "9"]
        return ["-c:a", "libmp3lame", "-b:a", _bitrate_from_quality(normalized)]
    if target_format == "wav":
        return ["-c:a", "pcm_s16le"]
    if target_format == "webm":
        return ["-c:a", "libopus", "-b:a", _bitrate_from_quality(audio_quality, best="160k")]
    return ["-c:a", "aac", "-b:a", _bitrate_from_quality(audio_quality)]


def normalized_output_path(input_path: str, target_format: str) -> str:
    """Return the final normalized path using the requested container extension."""
    return str(Path(input_path).with_suffix(f".{target_format.lower()}"))


def build_normalization_command(
    ffmpeg_path: str,
    input_path: str,
    temp_output_path: str,
    target_format: str,
    audio_quality: Any,
    audio_channels: int = AUDIO_CHANNELS,
    audio_sample_rate: int | None = None,
    video_codec: str | None = None,
) -> list[str]:
    """Build one FFmpeg pass that normalizes audio and produces the target format."""
    if not isinstance(audio_sample_rate, int) or isinstance(audio_sample_rate, bool):
        raise ValueError("Audio sample rate is required for normalization")
    if audio_sample_rate <= 0:
        raise ValueError("Audio sample rate is required for normalization")

    target_format = target_format.lower()
    input_extension = Path(input_path).suffix.lower().lstrip(".")
    args = [
        ffmpeg_path,
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        input_path,
    ]

    if target_format in VIDEO_FORMATS:
        args.extend(["-map", "0:v:0?", "-map", "0:a:0?", "-map_metadata", "0"])
        if target_format == "webm":
            args.extend(
                webm_video_encoding_args(
                    video_codec,
                    copy_when_unknown=input_extension == "webm",
                )
            )
        else:
            args.extend(["-c:v", "copy"])
        args.extend(_audio_codec_args(target_format, audio_quality))
    elif target_format in AUDIO_FORMATS:
        args.extend([
            "-map",
            "0:a:0?",
            "-map_metadata",
            "0",
            "-vn",
            "-ac",
            str(audio_channels),
        ])
        args.extend(_audio_codec_args(target_format, audio_quality))
    else:
        raise ValueError(f"Unsupported normalization format: {target_format}")

    audio_filter = f"{LOUDNORM_FILTER},aresample={audio_sample_rate}"
    args.extend(["-af", audio_filter])
    if target_format in ("mp4", "m4a"):
        args.extend(["-movflags", "+faststart"])
    args.append(temp_output_path)
    return args


def _remove_file(path: str, description: str) -> None:
    if not path:
        return
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        log.warning(f"Failed to remove {description} {path}: {exc}")


def normalize_media_file(
    input_path: str,
    settings: Mapping[str, Any],
    ffmpeg_path: str | None,
    stop_check: Callable[[], bool] | None = None,
) -> NormalizationResult:
    """Normalize a downloaded file, keeping output only when normalization succeeds."""
    if not input_path or not os.path.isfile(input_path):
        return NormalizationResult(False, input_path, "Downloaded file was not found for normalization")

    temp_path = ""
    normalization_succeeded = False
    cleanup_allowed = True
    try:
        if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
            return NormalizationResult(False, input_path, "FFmpeg executable was not found")

        target_format = str(settings.get("format", DEFAULT_FORMAT)).strip().lower()
        output_path = normalized_output_path(input_path, target_format)
        output = Path(output_path)
        temp_output = output.with_name(f".{output.stem}.{uuid4().hex}.normalize{output.suffix}")
        temp_path = str(temp_output)
        media_probe = probe_media_file(input_path, ffmpeg_path)
        effective_audio_sample_rate = media_probe.audio_sample_rate
        if effective_audio_sample_rate is None:
            return NormalizationResult(
                False,
                input_path,
                "Input audio sample rate could not be determined",
            )

        try:
            command = build_normalization_command(
                ffmpeg_path,
                input_path,
                temp_path,
                target_format,
                settings.get("audio_quality", DEFAULT_AUDIO_QUALITY),
                int(settings.get("audio_channels", AUDIO_CHANNELS)),
                effective_audio_sample_rate,
                media_probe.video_codec,
            )
        except (TypeError, ValueError) as exc:
            return NormalizationResult(False, input_path, str(exc))

        log.info(f"Normalizing audio with FFmpeg: {target_format}")
        execution = run_ffmpeg_command(
            command,
            stop_check=stop_check,
            timeout_sec=FFMPEG_NORMALIZE_TIMEOUT_SEC,
            timeout_error="Audio normalization timed out",
        )
        cleanup_allowed = execution.process_stopped
        if execution.paused:
            return NormalizationResult(
                False,
                input_path,
                MSG_PAUSED_BY_USER,
                paused=True,
            )
        if not execution.success:
            log.error(
                "Audio normalization failed: "
                f"{redact_urls_in_text(execution.error)}"
            )
            return NormalizationResult(False, input_path, execution.error)

        normalized_probe = probe_media_file(temp_path, ffmpeg_path)
        normalized_sample_rate = normalized_probe.audio_sample_rate
        if normalized_sample_rate != effective_audio_sample_rate:
            if normalized_sample_rate is None:
                error = "Normalized output sample rate could not be verified"
            else:
                error = (
                    "Normalized output sample rate changed "
                    f"from {effective_audio_sample_rate} Hz "
                    f"to {normalized_sample_rate} Hz"
                )
            log.error(error)
            return NormalizationResult(False, input_path, error)

        try:
            os.replace(temp_path, output_path)
            if os.path.normcase(os.path.abspath(input_path)) != os.path.normcase(os.path.abspath(output_path)):
                try:
                    os.remove(input_path)
                except OSError as exc:
                    log.warning(f"Normalized output created but source cleanup failed: {exc}")
            normalization_succeeded = True
            log.info(f"Audio normalization completed: {output_path}")
            return NormalizationResult(True, output_path)
        except OSError as exc:
            log.error(f"Audio normalization file commit failed: {exc}", exc_info=True)
            return NormalizationResult(False, input_path, str(exc))
    finally:
        if not normalization_succeeded:
            # Intentional product policy: when normalization was requested, the
            # unnormalized download is not a valid final artifact. Remove it on
            # failure, timeout, pause, or cancellation along with partial output.
            if cleanup_allowed:
                _remove_file(temp_path, "incomplete normalization file")
                _remove_file(input_path, "non-normalized downloaded file")
            else:
                log.error(
                    "Skipping normalization file cleanup because FFmpeg "
                    "termination could not be confirmed"
                )
