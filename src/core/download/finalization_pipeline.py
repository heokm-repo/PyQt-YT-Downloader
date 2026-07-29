"""Run one final media pass in the task workspace and commit only verified output."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Any, Callable, Mapping
from uuid import uuid4

from constants import FFMPEG_NORMALIZE_TIMEOUT_SEC, MSG_PAUSED_BY_USER
from core.download.ffmpeg_process import run_ffmpeg_command
from core.download.finalization_command import build_finalization_command
from core.download.finalization_policy import build_finalization_plan
from core.download.media_probe import probe_media_file
from core.download.webm_encoding import is_webm_audio_codec, is_webm_video_codec
from utils.logger import log


@dataclass(frozen=True)
class FinalizationResult:
    success: bool
    output_path: str
    error: str = ""
    paused: bool = False


def _verified_output(plan, source_probe, output_probe) -> str | None:
    if plan.target_format == "webm":
        output_audio = output_probe.audio_codec
        audio_was_lost = (
            source_probe.audio_codec is not None and output_audio is None
        )
        incompatible_audio = (
            output_audio is not None
            and not is_webm_audio_codec(output_audio)
        )
        if (
            not is_webm_video_codec(output_probe.video_codec)
            or audio_was_lost
            or incompatible_audio
        ):
            return "Final WebM codecs could not be verified"
    if plan.target_format == "m4a" and (
        output_probe.video_codec is not None
        or output_probe.audio_codec != "aac"
    ):
        return "Final M4A streams could not be verified"
    if plan.target_format == "mp4" and plan.compatibility:
        if (
            output_probe.video_codec != "h264"
            or output_probe.video_pixel_format != "yuv420p"
            or output_probe.audio_codec not in {None, "aac"}
        ):
            return "Final MP4 video compatibility could not be verified"
    if plan.audio_filter and output_probe.audio_sample_rate is None:
        return "Final audio sample rate could not be verified"
    return None


def finalize_and_commit_download(
    input_path: str,
    workspace: str,
    download_folder: str,
    settings: Mapping[str, Any],
    ffmpeg_path: str | None,
    stop_check: Callable[[], bool] | None = None,
) -> FinalizationResult:
    """Finalize inside workspace, then move the only completed file into downloads."""
    if not input_path or not os.path.isfile(input_path):
        return FinalizationResult(False, input_path, "Workspace output was not found")
    if not ffmpeg_path or not os.path.isfile(ffmpeg_path):
        return FinalizationResult(False, input_path, "FFmpeg executable was not found")

    input_probe = probe_media_file(input_path, ffmpeg_path)
    try:
        plan = build_finalization_plan(settings, input_probe, input_path)
    except (TypeError, ValueError) as exc:
        return FinalizationResult(False, input_path, str(exc))

    input_file = Path(input_path)
    final_name = f"{input_file.stem}.{plan.target_format}"
    destination = Path(download_folder, final_name)
    working_output = Path(
        workspace,
        f".{input_file.stem}.{uuid4().hex}.finalize.{plan.target_format}",
    )
    produced_path = input_path
    cleanup_allowed = True
    try:
        if plan.requires_ffmpeg:
            command = build_finalization_command(
                ffmpeg_path,
                input_path,
                str(working_output),
                plan,
            )
            execution = run_ffmpeg_command(
                command,
                stop_check=stop_check,
                timeout_sec=FFMPEG_NORMALIZE_TIMEOUT_SEC,
                timeout_error="Media finalization timed out",
            )
            cleanup_allowed = execution.process_stopped
            if execution.paused:
                return FinalizationResult(False, input_path, MSG_PAUSED_BY_USER, True)
            if not execution.success:
                return FinalizationResult(False, input_path, execution.error)
            produced_path = str(working_output)
            output_probe = probe_media_file(produced_path, ffmpeg_path)
            verification_error = _verified_output(
                plan,
                input_probe,
                output_probe,
            )
            if verification_error:
                return FinalizationResult(False, input_path, verification_error)

        os.makedirs(download_folder, exist_ok=True)
        os.replace(produced_path, destination)
        if produced_path != input_path and os.path.isfile(input_path):
            os.remove(input_path)
        return FinalizationResult(True, str(destination))
    except OSError as exc:
        return FinalizationResult(False, input_path, str(exc))
    finally:
        if cleanup_allowed and os.path.isfile(working_output):
            try:
                os.remove(working_output)
            except OSError as exc:
                log.debug(
                    "Failed to remove incomplete finalization output %s: %s",
                    working_output,
                    exc,
                )
