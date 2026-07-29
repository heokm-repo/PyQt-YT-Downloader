"""Finalize MP4 downloads for broad legacy-device compatibility."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Callable
from uuid import uuid4

from constants import FFMPEG_NORMALIZE_TIMEOUT_SEC, MSG_PAUSED_BY_USER
from core.download.ffmpeg_process import run_ffmpeg_command
from core.download.media_probe import MediaProbeResult, probe_media_file
from utils.logger import log


COMPATIBLE_VIDEO_CODEC = "h264"
COMPATIBLE_AUDIO_CODEC = "aac"
COMPATIBLE_PIXEL_FORMAT = "yuv420p"
DEFAULT_AAC_BITRATE = "192k"


@dataclass(frozen=True)
class CompatibilityFinalizationResult:
    success: bool
    output_path: str
    error: str = ""
    paused: bool = False


def build_compatibility_command(
    ffmpeg_path: str,
    input_path: str,
    output_path: str,
    probe: MediaProbeResult,
) -> list[str]:
    """Build a command that copies compatible streams and encodes the rest."""
    args = [
        ffmpeg_path,
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        input_path,
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-map_metadata",
        "0",
    ]
    if (
        probe.video_codec == COMPATIBLE_VIDEO_CODEC
        and probe.video_pixel_format == COMPATIBLE_PIXEL_FORMAT
    ):
        args.extend(["-c:v", "copy"])
    else:
        args.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                COMPATIBLE_PIXEL_FORMAT,
            ]
        )

    if probe.audio_codec == COMPATIBLE_AUDIO_CODEC:
        args.extend(["-c:a", "copy"])
    else:
        args.extend(["-c:a", "aac", "-b:a", DEFAULT_AAC_BITRATE])

    args.extend(["-movflags", "+faststart", output_path])
    return args


def _is_compatible(probe: MediaProbeResult) -> bool:
    return (
        probe.video_codec == COMPATIBLE_VIDEO_CODEC
        and probe.video_pixel_format == COMPATIBLE_PIXEL_FORMAT
        and (probe.audio_codec is None or probe.audio_codec == COMPATIBLE_AUDIO_CODEC)
    )


def finalize_mp4_compatibility(
    input_path: str,
    ffmpeg_path: str | None,
    stop_check: Callable[[], bool] | None = None,
) -> CompatibilityFinalizationResult:
    """Create and verify an H.264/AAC/yuv420p MP4, preserving the source on failure."""
    if not input_path or not os.path.isfile(input_path):
        return CompatibilityFinalizationResult(False, input_path, "Input file was not found")
    if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
        return CompatibilityFinalizationResult(
            False, input_path, "FFmpeg executable was not found"
        )

    probe = probe_media_file(input_path, ffmpeg_path)
    if probe.video_codec is None or probe.video_pixel_format is None:
        return CompatibilityFinalizationResult(
            False, input_path, "Input video codec could not be determined by FFprobe"
        )

    output = Path(input_path).with_suffix(".mp4")
    temp_path = str(
        output.with_name(f".{output.stem}.{uuid4().hex}.compatibility.mp4")
    )
    committed = False
    cleanup_allowed = True
    try:
        command = build_compatibility_command(
            ffmpeg_path, input_path, temp_path, probe
        )
        log.info(
            "Finalizing universal MP4 compatibility (input compatible: %s)",
            _is_compatible(probe),
        )
        execution = run_ffmpeg_command(
            command,
            stop_check=stop_check,
            timeout_sec=FFMPEG_NORMALIZE_TIMEOUT_SEC,
            timeout_error="Universal compatibility finalization timed out",
        )
        cleanup_allowed = execution.process_stopped
        if execution.paused:
            return CompatibilityFinalizationResult(
                False, input_path, MSG_PAUSED_BY_USER, paused=True
            )
        if not execution.success:
            return CompatibilityFinalizationResult(
                False, input_path, execution.error
            )

        output_probe = probe_media_file(temp_path, ffmpeg_path)
        if not _is_compatible(output_probe):
            return CompatibilityFinalizationResult(
                False,
                input_path,
                "Final MP4 compatibility could not be verified by FFprobe",
            )

        os.replace(temp_path, str(output))
        if os.path.normcase(os.path.abspath(input_path)) != os.path.normcase(
            os.path.abspath(str(output))
        ):
            os.remove(input_path)
        committed = True
        return CompatibilityFinalizationResult(True, str(output))
    except OSError as exc:
        return CompatibilityFinalizationResult(False, input_path, str(exc))
    finally:
        if not committed and cleanup_allowed and os.path.isfile(temp_path):
            try:
                os.remove(temp_path)
            except OSError as exc:
                log.warning("Failed to remove compatibility temporary file: %s", exc)
