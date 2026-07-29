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


def _stream_for_progress(
    progress_info: Dict[str, Any],
    clean_current: str,
) -> Dict[str, Any]:
    streams = progress_info["streams"]
    for stream in streams:
        if stream.get("filename") == clean_current and clean_current:
            return stream

    active_index = min(
        progress_info.get("active_stream_index", 0),
        max(len(streams) - 1, 0),
    )
    if not streams:
        streams.append(
            {
                "id": "dynamic-0",
                "kind": "unknown",
                "downloaded": 0,
                "total": 0,
                "filename": clean_current or None,
            }
        )
        return streams[0]

    stream = streams[active_index]
    if clean_current and not stream.get("filename"):
        stream["filename"] = clean_current
    elif clean_current and stream.get("filename") != clean_current:
        for index, candidate in enumerate(streams):
            if not candidate.get("filename"):
                candidate["filename"] = clean_current
                progress_info["active_stream_index"] = index
                return candidate
    return stream


def _apply_selected_stream_progress(
    d: Dict[str, Any],
    progress_info: Dict[str, Any],
) -> None:
    current_total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
    downloaded = d.get("downloaded_bytes", 0) or 0
    clean_current = clean_progress_filename(d.get("filename", ""))
    stream = _stream_for_progress(progress_info, clean_current)
    stream["downloaded"] = downloaded
    if current_total > 0:
        stream["total"] = current_total

    total_plan = sum(stream.get("total", 0) or 0 for stream in progress_info["streams"])
    cumulative = sum(
        stream.get("downloaded", 0) or 0 for stream in progress_info["streams"]
    )
    if total_plan <= 0:
        total_plan = current_total if current_total > 0 else 1
    progress_info["total_size_est"] = total_plan
    percent = min((cumulative / total_plan) * 100, 100.0)
    d["_percent_str"] = f"{percent:.1f}%"
    d["downloaded_bytes"] = cumulative
    d["total_bytes"] = total_plan
    d["total_bytes_estimate"] = total_plan
    speed = d.get("speed")
    if speed:
        d["_speed_str"] = format_speed(speed)


def apply_downloading_progress(d: Dict[str, Any], progress_info: Dict[str, Any]) -> None:
    """Mutate progress payload with cumulative video/audio progress."""
    if "streams" in progress_info:
        _apply_selected_stream_progress(d, progress_info)
        return

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
    elif clean_current and saved_video_name is None and saved_audio_name is None:
        progress_info["video"]["filename"] = clean_current
        is_video_file = True
    elif clean_current and saved_video_name is None:
        progress_info["video"]["filename"] = clean_current
        is_video_file = True
    elif clean_current and saved_audio_name is None:
        progress_info["audio"]["filename"] = clean_current
        is_audio_file = True
    elif progress_info.get("active_stream", "video") == "audio":
        is_audio_file = True
    else:
        is_video_file = True

    if is_video_file:
        progress_info["video"]["downloaded"] = downloaded
        if current_real_total > 0:
            progress_info["video"]["total"] = current_real_total
    elif is_audio_file:
        progress_info["audio"]["downloaded"] = downloaded
        if current_real_total > 0:
            progress_info["audio"]["total"] = current_real_total

    video_total = progress_info["video"]["total"]
    audio_total = progress_info["audio"]["total"]
    audio_est = progress_info.get("audio_size_est", 0)

    if audio_total <= 0 and audio_est > 0:
        current_total_plan = video_total + audio_est
    else:
        current_total_plan = video_total + audio_total

    if current_total_plan <= 0:
        current_total_plan = current_real_total if current_real_total > 0 else 1

    cumulative_downloaded = (
        progress_info["video"]["downloaded"]
        + progress_info["audio"]["downloaded"]
    )
    if not is_video_file and not is_audio_file:
        cumulative_downloaded = downloaded

    progress_info["total_size_est"] = current_total_plan

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
        if "streams" in progress_info:
            streams = progress_info["streams"]
            if streams:
                clean_current = clean_progress_filename(d.get("filename", ""))
                stream = _stream_for_progress(progress_info, clean_current)
                if stream.get("total", 0) > 0:
                    stream["downloaded"] = stream["total"]
                active_index = progress_info.get("active_stream_index", 0)
                if active_index < len(streams) - 1:
                    progress_info["active_stream_index"] = active_index + 1
                    return False

            d["_percent_str"] = "100%"
            d["_speed_str"] = STR.WORKER_MSG_COMPLETED
            total_size = progress_info.get("total_size_est", 0)
            if total_size > 0:
                d["downloaded_bytes"] = total_size
                d["total_bytes"] = total_size
                d["total_bytes_estimate"] = total_size
            return True

        clean_current = clean_progress_filename(d.get("filename", ""))
        saved_audio_name = progress_info["audio"].get("filename")
        if saved_audio_name:
            saved_audio_name = os.path.basename(saved_audio_name)
        is_audio_file = bool(saved_audio_name and clean_current == saved_audio_name)

        active_stream = progress_info.get("active_stream", "video")
        if active_stream == "video" and not is_audio_file:
            video = progress_info.get("video")
            if video and video["total"] > 0:
                video["downloaded"] = video["total"]
            progress_info["active_stream"] = "audio"
            return False

        audio_total = progress_info["audio"]["total"]

        if audio_total > 0 and not is_audio_file and active_stream != "audio":
            return False

        d["_percent_str"] = "100%"
        d["_speed_str"] = STR.WORKER_MSG_COMPLETED

        total_size = progress_info.get("total_size_est", 0)
        if total_size > 0:
            d["downloaded_bytes"] = total_size
            d["total_bytes"] = total_size
            d["total_bytes_estimate"] = total_size

    return True
