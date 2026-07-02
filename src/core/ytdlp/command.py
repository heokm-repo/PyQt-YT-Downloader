"""Build yt-dlp CLI commands from option dictionaries."""

from typing import Any

from constants import YTDLP_RETRIES


def build_command(
    ytdlp_path: str,
    ffmpeg_path: str | None,
    url: str,
    options: dict[str, Any],
    is_resume: bool = False,
) -> list[str]:
    args = [ytdlp_path, "--newline"]

    if "outtmpl" in options:
        args.extend(["--output", options["outtmpl"]])

    if "format" in options:
        args.extend(["--format", options["format"]])

    if "merge_output_format" in options:
        args.extend(["--merge-output-format", options["merge_output_format"]])

    if "recode_video" in options:
        args.extend(["--recode-video", options["recode_video"]])

    if "ffmpeg_location" in options:
        args.extend(["--ffmpeg-location", options["ffmpeg_location"]])
    elif ffmpeg_path:
        args.extend(["--ffmpeg-location", ffmpeg_path])

    if options.get("noplaylist"):
        args.append("--no-playlist")

    if options.get("extract_audio"):
        args.append("--extract-audio")

        if "audio_format" in options:
            args.extend(["--audio-format", options["audio_format"]])

        if "audio_quality" in options:
            args.extend(["--audio-quality", str(options["audio_quality"])])

    _add_postprocessor_args(args, options)

    if "cookiefile" in options:
        args.extend(["--cookies", options["cookiefile"]])

    if "js_runtimes" in options:
        args.extend(["--js-runtimes", options["js_runtimes"]])

    if "concurrent_fragment_downloads" in options:
        args.extend(["--concurrent-fragments", str(options["concurrent_fragment_downloads"])])

    if "home_path" in options:
        args.extend(["--paths", f"home:{options['home_path']}"])

    if "temp_path" in options:
        args.extend(["--paths", f"temp:{options['temp_path']}"])

    if is_resume:
        args.append("--no-overwrites")
    elif options.get("overwrites"):
        args.append("--force-overwrites")

    args.append("--no-warnings")
    args.append("--continue")
    args.append("--fragment-retries")
    args.append(YTDLP_RETRIES)
    args.append(url)

    return args


def _add_postprocessor_args(args: list[str], options: dict[str, Any]) -> None:
    pp_args = options.get("postprocessor_args")
    if not pp_args or "ffmpeg" not in pp_args:
        return

    ffmpeg_args = pp_args["ffmpeg"]
    i = 0
    while i < len(ffmpeg_args):
        arg = ffmpeg_args[i]
        if i + 1 < len(ffmpeg_args):
            value = ffmpeg_args[i + 1]
            args.extend(["--postprocessor-args", f"ffmpeg:{arg} {value}"])
            i += 2
        else:
            args.extend(["--postprocessor-args", f"ffmpeg:{arg}"])
            i += 1
