"""WebM codec compatibility and video encoding arguments."""

from __future__ import annotations


WEBM_COPY_VIDEO_CODECS = frozenset({"av1", "vp8", "vp9"})
WEBM_COPY_AUDIO_CODECS = frozenset({"opus", "vorbis"})
def is_webm_video_codec(codec: str | None) -> bool:
    return str(codec or "").strip().lower() in WEBM_COPY_VIDEO_CODECS


def is_webm_audio_codec(codec: str | None) -> bool:
    return str(codec or "").strip().lower() in WEBM_COPY_AUDIO_CODECS
