"""Create the single FFmpeg command used for final media output."""

from core.download.finalization_policy import FinalizationPlan


def build_finalization_command(
    ffmpeg_path: str,
    input_path: str,
    output_path: str,
    plan: FinalizationPlan,
) -> list[str]:
    args = [
        ffmpeg_path, "-y", "-nostdin", "-loglevel", "error", "-i", input_path,
    ]
    if plan.audio_only:
        args.extend(["-map", "0:a:0?", "-map_metadata", "0", "-vn", "-ac", str(plan.audio_channels)])
    else:
        args.extend(["-map", "0:v:0?", "-map", "0:a:0?", "-map_metadata", "0"])
        args.extend(plan.video_args)
    args.extend(plan.audio_args)
    if plan.audio_filter:
        args.extend(["-af", plan.audio_filter])
    if plan.target_format in {"mp4", "m4a"}:
        args.extend(["-movflags", "+faststart"])
    args.append(output_path)
    return args
