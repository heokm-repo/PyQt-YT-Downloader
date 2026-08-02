"""Verify finalized media streams before publishing a download."""

from __future__ import annotations

from core.download.finalization_policy import FinalizationPlan
from core.download.media_probe import MediaProbeResult
from core.download.webm_encoding import is_webm_audio_codec, is_webm_video_codec


def verify_finalized_output(
    plan: FinalizationPlan,
    source_probe: MediaProbeResult,
    output_probe: MediaProbeResult,
) -> str | None:
    """Return a verification error, or ``None`` for a valid final output."""
    output_audio = output_probe.audio_codec
    output_video = output_probe.video_codec

    if plan.audio_only and output_audio is None:
        return "Final audio stream could not be verified"

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
            return "Final WebM codecs could not be verified"

    if not plan.audio_only and output_video is None:
        return "Final video stream could not be verified"

    if plan.target_format == "m4a" and (
        output_video is not None or output_audio != "aac"
    ):
        return "Final M4A streams could not be verified"

    if plan.target_format == "mp3" and output_audio != "mp3":
        return "Final MP3 codec could not be verified"

    if plan.target_format == "wav" and output_audio != "pcm_s16le":
        return "Final WAV codec could not be verified"

    if plan.target_format == "mp4":
        if output_audio not in {None, "aac"}:
            return "Final MP4 streams could not be verified"
        if plan.compatibility and (
            output_video != "h264"
            or output_probe.video_pixel_format != "yuv420p"
        ):
            return "Final MP4 video compatibility could not be verified"

    if source_probe.audio_codec is not None and output_audio is None:
        return "Final audio stream was lost"

    if plan.audio_filter:
        if output_probe.audio_sample_rate is None:
            return "Final audio sample rate could not be verified"
        if output_probe.audio_sample_rate != source_probe.audio_sample_rate:
            return "Final audio sample rate did not match the source"

    return None
