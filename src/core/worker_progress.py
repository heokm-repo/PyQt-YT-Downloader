"""Progress calculations used by DownloadWorker."""

import os
from typing import Any, Dict

from constants import (
    BYTES_PER_KB, BYTES_PER_MB, EXT_PART, EXT_YTDL,
    STATUS_FINISHED, STATUS_POSTPROCESSING,
)
from locales.strings import STR


def clean_progress_filename(filename: str) -> str:
    """Return a comparable filename from yt-dlp progress data."""
    clean_name = os.path.basename(filename or "")
    for ext in [EXT_PART, EXT_YTDL]:
        if clean_name.endswith(ext):
            return clean_name[:-len(ext)]
    return clean_name


def format_speed(speed: float) -> str:
    """Convert bytes per second into a readable speed string."""
    if speed > BYTES_PER_MB:
        return f"{speed / BYTES_PER_MB:.1f} MB/s"
    return f"{speed / BYTES_PER_KB:.1f} KB/s"


def apply_downloading_progress(d: Dict[str, Any], progress_info: Dict[str, Any]) -> None:
    """Mutate progress payload with cumulative video/audio progress."""
    current_real_total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
    downloaded = d.get("downloaded_bytes", 0) or 0
    clean_current = clean_progress_filename(d.get("filename", ""))

    saved_video_name = progress_info["video"].get("filename")
    if saved_video_name:
        saved_video_name = os.path.basename(saved_video_name)

    saved_audio_name = progress_info["audio"].get("filename")
    if saved_audio_name:
        saved_audio_name = os.path.basename(saved_audio_name)

    is_video_file = False
    is_audio_file = False

    if saved_video_name and clean_current == saved_video_name:
        is_video_file = True
    elif saved_audio_name and clean_current == saved_audio_name:
        is_audio_file = True
    elif saved_video_name is None and saved_audio_name is None:
        progress_info["video"]["filename"] = clean_current
        is_video_file = True
    elif saved_video_name is None:
        progress_info["video"]["filename"] = clean_current
        is_video_file = True
    elif saved_audio_name is None:
        progress_info["audio"]["filename"] = clean_current
        is_audio_file = True

    if is_video_file:
        progress_info["video"]["downloaded"] = downloaded
        cumulative_downloaded = downloaded
    elif is_audio_file:
        progress_info["audio"]["downloaded"] = downloaded
        cumulative_downloaded = progress_info["video"]["total"] + downloaded
    else:
        cumulative_downloaded = downloaded

    video_total = progress_info["video"]["total"]
    audio_total = progress_info["audio"]["total"]
    audio_est = progress_info.get("audio_size_est", 0)

    if audio_total <= 0 and audio_est > 0:
        current_total_plan = video_total + audio_est
    else:
        current_total_plan = video_total + audio_total

    if current_total_plan <= 0:
        current_total_plan = current_real_total if current_real_total > 0 else 1

    percent = (cumulative_downloaded / current_total_plan) * 100
    if percent > 100.0:
        percent = 100.0

    d["_percent_str"] = f"{percent:.1f}%"
    d["downloaded_bytes"] = cumulative_downloaded
    d["total_bytes"] = current_total_plan
    d["total_bytes_estimate"] = current_total_plan

    speed = d.get("speed")
    if speed:
        d["_speed_str"] = format_speed(speed)


def apply_postprocessing_progress(d: Dict[str, Any], status: str, progress_info: Dict[str, Any]) -> bool:
    """Mutate postprocessing payload and return whether it should be emitted."""
    if status == STATUS_POSTPROCESSING:
        d["_percent_str"] = STR.WORKER_MSG_PROCESSING
        d["_speed_str"] = STR.WORKER_MSG_CONVERTING

        total_size = progress_info.get("total_size_est", 0)
        if total_size > 0:
            d["downloaded_bytes"] = total_size
            d["total_bytes"] = total_size
            d["total_bytes_estimate"] = total_size

    elif status == STATUS_FINISHED:
        clean_current = clean_progress_filename(d.get("filename", ""))

        saved_audio_name = progress_info["audio"].get("filename")
        if saved_audio_name:
            saved_audio_name = os.path.basename(saved_audio_name)

        audio_total = progress_info["audio"]["total"]
        is_audio_file = bool(saved_audio_name and clean_current == saved_audio_name)

        if audio_total > 0 and not is_audio_file:
            return False

        d["_percent_str"] = "100%"
        d["_speed_str"] = STR.WORKER_MSG_COMPLETED

        total_size = progress_info.get("total_size_est", 0)
        if total_size > 0:
            d["downloaded_bytes"] = total_size
            d["total_bytes"] = total_size
            d["total_bytes_estimate"] = total_size

    return True
