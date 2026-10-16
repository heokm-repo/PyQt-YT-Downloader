"""Verify finalized media streams before publishing a download."""

from __future__ import annotations

from core.download.finalization_policy import FinalizationPlan
from core.download.media_probe import MediaProbeResult
from core.download.webm_encoding import is_webm_audio_codec, is_webm_video_codec
from locales.strings import STR


def verify_finalized_output(
    plan: FinalizationPlan,
    source_probe: MediaProbeResult,
    output_probe: MediaProbeResult,
) -> str | None:
    """Return a verification error, or ``None`` for a valid final output."""
    output_audio = output_probe.audio_codec
    output_video = output_probe.video_codec

    if plan.audio_only and output_audio is None:
        return STR.ERR_FINAL_AUDIO_VERIFY

    if plan.target_format == "webm":
        audio_was_lost = (
            source_probe.audio_codec is not None and output_audio is None
        )
        incompatible_audio = (
            output_audio is not None
            and not is_webm_audio_codec(output_audio)
        )
        if (
            not is_webm_video_codec(output_video)
            or audio_was_lost
            or incompatible_audio
        ):
            return STR.ERR_FINAL_FORMAT_VERIFY_FMT.format(format="WebM")

    if not plan.audio_only and output_video is None:
        return STR.ERR_FINAL_VIDEO_VERIFY

    if plan.target_format == "m4a" and (
        output_video is not None or output_audio != "aac"
    ):
        return STR.ERR_FINAL_FORMAT_VERIFY_FMT.format(format="M4A")

    if plan.target_format == "mp3" and output_audio != "mp3":
        return STR.ERR_FINAL_FORMAT_VERIFY_FMT.format(format="MP3")

    if plan.target_format == "wav" and output_audio != "pcm_s16le":
        return STR.ERR_FINAL_FORMAT_VERIFY_FMT.format(format="WAV")

    if plan.target_format == "mp4":
        if output_audio not in {None, "aac"}:
            return STR.ERR_FINAL_FORMAT_VERIFY_FMT.format(format="MP4")
        if plan.compatibility and (
            output_video != "h264"
            or output_probe.video_pixel_format != "yuv420p"
        ):
            return STR.ERR_FINAL_COMPAT_VERIFY

    if source_probe.audio_codec is not None and output_audio is None:
        return STR.ERR_FINAL_AUDIO_LOST

    if plan.audio_filter:
        if output_probe.audio_sample_rate is None:
            return STR.ERR_FINAL_SAMPLE_RATE_VERIFY
        if output_probe.audio_sample_rate != source_probe.audio_sample_rate:
            return STR.ERR_FINAL_SAMPLE_RATE_MISMATCH

    return None
