"""Finalize video audio quality and exact WebM container compatibility."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
from typing import Callable
from uuid import uuid4

from constants import FFMPEG_NORMALIZE_TIMEOUT_SEC, MSG_PAUSED_BY_USER
from core.download.ffmpeg_process import run_ffmpeg_command
from core.download.media_probe import probe_media_file
from core.download.webm_encoding import (
    is_webm_audio_codec,
    is_webm_video_codec,
    webm_video_encoding_args,
)
from utils.logger import log
from utils.url_security import redact_urls_in_text


SUPPORTED_VIDEO_FORMATS = frozenset({"mp4", "mkv", "webm"})
WEBM_BEST_ENCODING_BITRATE = "160k"


@dataclass(frozen=True)
class AudioFinalizationResult:
    success: bool
    output_path: str
    error: str = ""
    paused: bool = False


def _validated_bitrate(bitrate: str) -> str:
    normalized = str(bitrate or "").strip().lower()
    match = re.fullmatch(r"(\d+)k", normalized)
    if not match or int(match.group(1)) <= 0:
        raise ValueError("A positive audio bitrate is required")
    return normalized


def build_audio_finalization_command(
    ffmpeg_path: str,
    input_path: str,
    temp_output_path: str,
    target_format: str,
    audio_bitrate: str | None,
    audio_sample_rate: int,
    video_codec: str | None = None,
    audio_codec: str | None = None,
) -> list[str]:
    """Build a selective stream copy/encode FFmpeg command."""
    normalized_format = str(target_format or "").strip().lower()
    if normalized_format not in SUPPORTED_VIDEO_FORMATS:
        raise ValueError(
            f"Unsupported audio finalization format: {normalized_format}"
        )
    if (
        not isinstance(audio_sample_rate, int)
        or isinstance(audio_sample_rate, bool)
        or audio_sample_rate <= 0
    ):
        raise ValueError("Audio sample rate is required for finalization")

    args = [
        ffmpeg_path,
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        input_path,
    ]
    if normalized_format == "webm":
        args.extend(
            [
                "-map",
                "0:v:0?",
                "-map",
                "0:a:0?",
                "-map_metadata",
                "0",
            ]
        )
        args.extend(webm_video_encoding_args(video_codec))
        if audio_bitrate is None and is_webm_audio_codec(audio_codec):
            args.extend(["-c:a", "copy"])
        else:
            args.extend(
                [
                    "-c:a",
                    "libopus",
                    "-b:a",
                    _validated_bitrate(
                        audio_bitrate or WEBM_BEST_ENCODING_BITRATE
                    ),
                    "-ar",
                    str(audio_sample_rate),
                ]
            )
    else:
        args.extend(
            [
                "-map",
                "0",
                "-dn",
                "-ignore_unknown",
                "-map_metadata",
                "0",
                "-c",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                _validated_bitrate(audio_bitrate or ""),
                "-ar",
                str(audio_sample_rate),
            ]
        )
        if normalized_format == "mp4":
            args.extend(["-c:s", "mov_text", "-movflags", "+faststart"])
    args.append(temp_output_path)
    return args


def _remove_temporary_file(path: str) -> None:
    if not path:
        return
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError as exc:
        log.warning(f"Failed to remove incomplete audio finalization file {path}: {exc}")


def finalize_video_audio_quality(
    input_path: str,
    target_format: str,
    audio_bitrate: str | None,
    ffmpeg_path: str | None,
    stop_check: Callable[[], bool] | None = None,
) -> AudioFinalizationResult:
    """Finalize requested quality/container and atomically keep the result."""
    if not input_path or not os.path.isfile(input_path):
        return AudioFinalizationResult(
            False,
            input_path,
            "Downloaded file was not found for audio finalization",
        )
    if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
        return AudioFinalizationResult(
            False,
            input_path,
            "FFmpeg executable was not found",
        )

    normalized_format = str(target_format or "").strip().lower()
    if normalized_format not in SUPPORTED_VIDEO_FORMATS:
        return AudioFinalizationResult(
            False,
            input_path,
            f"Unsupported audio finalization format: {normalized_format}",
        )
    output_path = str(Path(input_path).with_suffix(f".{normalized_format}"))
    output = Path(output_path)
    temp_path = str(
        output.with_name(
            f".{output.stem}.{uuid4().hex}.audio-quality{output.suffix}"
        )
    )
    finalization_succeeded = False
    cleanup_allowed = True

    try:
        input_probe = probe_media_file(input_path, ffmpeg_path)
        input_sample_rate = input_probe.audio_sample_rate
        if input_sample_rate is None:
            return AudioFinalizationResult(
                False,
                input_path,
                "Input audio sample rate could not be determined",
            )
        if normalized_format == "webm" and input_probe.video_codec is None:
            return AudioFinalizationResult(
                False,
                input_path,
                "Input video codec could not be determined",
            )

        if (
            normalized_format == "webm"
            and Path(input_path).suffix.lower() == ".webm"
            and audio_bitrate is None
            and is_webm_video_codec(input_probe.video_codec)
            and is_webm_audio_codec(input_probe.audio_codec)
        ):
            finalization_succeeded = True
            return AudioFinalizationResult(True, input_path)

        try:
            command = build_audio_finalization_command(
                ffmpeg_path,
                input_path,
                temp_path,
                normalized_format,
                audio_bitrate,
                input_sample_rate,
                input_probe.video_codec,
                input_probe.audio_codec,
            )
        except (TypeError, ValueError) as exc:
            return AudioFinalizationResult(False, input_path, str(exc))

        log.info(
            "Applying final audio quality with FFmpeg: "
            f"{normalized_format}, {audio_bitrate or 'best'}"
        )
        execution = run_ffmpeg_command(
            command,
            stop_check=stop_check,
            timeout_sec=FFMPEG_NORMALIZE_TIMEOUT_SEC,
            timeout_error="Audio quality finalization timed out",
        )
        cleanup_allowed = execution.process_stopped
        if execution.paused:
            return AudioFinalizationResult(
                False,
                input_path,
                MSG_PAUSED_BY_USER,
                paused=True,
            )
        if not execution.success:
            log.error(
                "Audio quality finalization failed: "
                f"{redact_urls_in_text(execution.error)}"
            )
            return AudioFinalizationResult(False, input_path, execution.error)

        output_probe = probe_media_file(temp_path, ffmpeg_path)
        if output_probe.audio_sample_rate != input_sample_rate:
            if output_probe.audio_sample_rate is None:
                error = "Final audio sample rate could not be verified"
            else:
                error = (
                    "Final audio sample rate changed "
                    f"from {input_sample_rate} Hz "
                    f"to {output_probe.audio_sample_rate} Hz"
                )
            log.error(error)
            return AudioFinalizationResult(False, input_path, error)
        if (
            normalized_format == "webm"
            and not is_webm_video_codec(output_probe.video_codec)
        ):
            error = "Final WebM video codec could not be verified"
            log.error(error)
            return AudioFinalizationResult(False, input_path, error)

        try:
            os.replace(temp_path, output_path)
            if os.path.normcase(os.path.abspath(input_path)) != os.path.normcase(
                os.path.abspath(output_path)
            ):
                try:
                    os.remove(input_path)
                except OSError as exc:
                    log.warning(
                        "Audio-quality output created but source cleanup failed: "
                        f"{exc}"
                    )
        except OSError as exc:
            log.error(f"Audio quality file commit failed: {exc}", exc_info=True)
            return AudioFinalizationResult(False, input_path, str(exc))

        finalization_succeeded = True
        return AudioFinalizationResult(True, output_path)
    finally:
        if not finalization_succeeded and cleanup_allowed:
            # Unlike normalization, quality-finalization failure keeps the exact
            # downloaded source so a non-destructive retry remains possible.
            _remove_temporary_file(temp_path)
        elif not finalization_succeeded:
            log.error(
                "Skipping audio-quality temporary cleanup because FFmpeg "
                "termination could not be confirmed"
            )
