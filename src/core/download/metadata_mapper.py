"""Map yt-dlp info dictionaries into app metadata dictionaries."""

from collections.abc import Mapping
from typing import Any

from constants import DEFAULT_PLAYLIST_TITLE, DEFAULT_UPLOADER, DEFAULT_VIDEO_TITLE


def build_metadata_result(info: Mapping[str, Any], clean_url: str, is_playlist: bool) -> dict[str, Any]:
    extractor = _extract_extractor(info)

    if is_playlist or info.get("_type") == "playlist":
        return {
            "title": info.get("title", DEFAULT_PLAYLIST_TITLE),
            "uploader": info.get("uploader", DEFAULT_UPLOADER),
            "is_playlist": True,
            "video_count": len(info.get("entries", [])),
            "extractor": extractor,
        }

    video_info = info
    if "entries" in info:
        video_info = info["entries"][0]
        extractor = _extract_extractor(video_info, extractor)

    download_streams = selected_download_streams(video_info)
    video_size, audio_size = estimate_media_sizes(video_info)

    result = {
        "title": video_info.get("title", DEFAULT_VIDEO_TITLE),
        "uploader": video_info.get("uploader", video_info.get("channel", DEFAULT_UPLOADER)),
        "duration": video_info.get("duration", 0),
        "thumbnail": video_info.get("thumbnail"),
        "id": video_info.get("id"),
        "extractor": extractor,
        "webpage_url": video_info.get("webpage_url", clean_url),
        "video_size": video_size,
        "audio_size": audio_size,
        "download_streams": download_streams,
    }
    audio_bitrate = selected_audio_bitrate(video_info)
    if audio_bitrate is not None:
        result["audio_bitrate"] = audio_bitrate
    return result


def _has_codec(value: object) -> bool:
    return str(value or "").strip().lower() not in {"", "none"}


def selected_download_streams(info: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Describe only the streams yt-dlp selected for this download."""
    candidates = None
    for key in ("requested_formats", "requested_downloads"):
        value = info.get(key)
        if isinstance(value, list) and value:
            candidates = [item for item in value if isinstance(item, Mapping)]
            break
    if candidates is None:
        candidates = [info]

    streams = []
    for index, fmt in enumerate(candidates):
        has_video = _has_codec(fmt.get("vcodec"))
        has_audio = _has_codec(fmt.get("acodec"))
        if not has_video and not has_audio:
            continue
        if has_video and has_audio:
            kind = "combined"
        elif has_video:
            kind = "video"
        else:
            kind = "audio"
        size = fmt.get("filesize", 0) or fmt.get("filesize_approx", 0) or 0
        streams.append(
            {
                "id": str(fmt.get("format_id") or index),
                "kind": kind,
                "size": size,
            }
        )
    return streams


def estimate_media_sizes(info: Mapping[str, Any]) -> tuple[int, int]:
    video_size = 0
    audio_size = 0

    if "requested_formats" in info:
        for fmt in info["requested_formats"]:
            size = fmt.get("filesize", 0) or fmt.get("filesize_approx", 0)
            if fmt.get("vcodec") != "none":
                video_size = size
            elif fmt.get("acodec") != "none":
                audio_size = size
    else:
        size = info.get("filesize", 0) or info.get("filesize_approx", 0)
        if info.get("vcodec") != "none":
            video_size = size
        elif info.get("acodec") != "none":
            audio_size = size

    if video_size == 0 and audio_size == 0:
        formats = info.get("formats", [])
        if formats:
            video_size = max(
                [fmt.get("filesize", 0) or fmt.get("filesize_approx", 0) for fmt in formats if fmt.get("vcodec") != "none"],
                default=0,
            )
            audio_size = max(
                [fmt.get("filesize", 0) or fmt.get("filesize_approx", 0) for fmt in formats if fmt.get("acodec") != "none"],
                default=0,
            )

    return video_size, audio_size


def selected_audio_sample_rate(info: Mapping[str, Any]) -> int | None:
    """Return the selected source audio sample rate when yt-dlp reports it."""
    candidates = []
    for key in ("requested_formats", "requested_downloads"):
        values = info.get(key)
        if isinstance(values, list):
            candidates.extend(value for value in values if isinstance(value, Mapping))
    candidates.append(info)

    for candidate in candidates:
        if candidate.get("acodec") == "none":
            continue
        sample_rate = candidate.get("asr") or candidate.get("audio_sample_rate")
        try:
            normalized_rate = int(float(sample_rate))
        except (TypeError, ValueError):
            continue
        if normalized_rate > 0:
            return normalized_rate
    return None


def selected_audio_bitrate(info: Mapping[str, Any]) -> int | None:
    """Return the selected audio bitrate in bits per second when reported."""
    candidates = []
    for key in ("requested_formats", "requested_downloads"):
        values = info.get(key)
        if isinstance(values, list):
            candidates.extend(value for value in values if isinstance(value, Mapping))
    candidates.append(info)

    for candidate in candidates:
        if candidate.get("acodec") == "none":
            continue
        bitrate_kbps = candidate.get("abr")
        try:
            normalized = int(float(bitrate_kbps) * 1000)
        except (TypeError, ValueError):
            normalized = 0
        if normalized > 0:
            return normalized

        if candidate.get("vcodec") == "none":
            size = candidate.get("filesize") or candidate.get("filesize_approx")
            duration = candidate.get("duration") or info.get("duration")
            try:
                calculated = int(float(size) * 8 / float(duration))
            except (TypeError, ValueError, ZeroDivisionError):
                calculated = 0
            if calculated > 0:
                return calculated
    return None


def _extract_extractor(info: Mapping[str, Any], default: str = "unknown") -> str:
    extractor = info.get("extractor", info.get("extractor_key", default))
    return extractor.lower() if extractor else extractor
