"""WebM codec compatibility and video encoding arguments."""

from __future__ import annotations


WEBM_COPY_VIDEO_CODECS = frozenset({"av1", "vp8", "vp9"})
WEBM_COPY_AUDIO_CODECS = frozenset({"opus", "vorbis"})
WEBM_VP9_ENCODING_ARGS = (
    "-c:v",
    "libvpx-vp9",
    "-crf",
    "30",
    "-b:v",
    "0",
    "-deadline",
    "good",
    "-cpu-used",
    "2",
    "-row-mt",
    "1",
)


def is_webm_video_codec(codec: str | None) -> bool:
    return str(codec or "").strip().lower() in WEBM_COPY_VIDEO_CODECS


def is_webm_audio_codec(codec: str | None) -> bool:
    return str(codec or "").strip().lower() in WEBM_COPY_AUDIO_CODECS


def webm_video_encoding_args(
    video_codec: str | None,
    *,
    copy_when_unknown: bool = False,
) -> tuple[str, ...]:
    normalized_codec = str(video_codec or "").strip().lower()
    if normalized_codec in WEBM_COPY_VIDEO_CODECS:
        return ("-c:v", "copy")
    if not normalized_codec and copy_when_unknown:
        return ("-c:v", "copy")
    return WEBM_VP9_ENCODING_ARGS
