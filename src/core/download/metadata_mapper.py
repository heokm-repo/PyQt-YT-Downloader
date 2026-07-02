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

    video_size, audio_size = estimate_media_sizes(video_info)

    return {
        "title": video_info.get("title", DEFAULT_VIDEO_TITLE),
        "uploader": video_info.get("uploader", video_info.get("channel", DEFAULT_UPLOADER)),
        "duration": video_info.get("duration", 0),
        "thumbnail": video_info.get("thumbnail"),
        "id": video_info.get("id"),
        "extractor": extractor,
        "webpage_url": video_info.get("webpage_url", clean_url),
        "video_size": video_size,
        "audio_size": audio_size,
    }


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


def _extract_extractor(info: Mapping[str, Any], default: str = "unknown") -> str:
    extractor = info.get("extractor", info.get("extractor_key", default))
    return extractor.lower() if extractor else extractor
