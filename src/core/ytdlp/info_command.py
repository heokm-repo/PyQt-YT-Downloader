"""Build yt-dlp commands for metadata extraction."""

from typing import Any, Dict, List, Optional

from constants import DEFAULT_ENCODING


def build_extract_info_command(
    ytdlp_path: str,
    url: str,
    options: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Convert extract_info options into yt-dlp CLI arguments."""
    dump_option = (
        "--dump-single-json"
        if options and options.get("dump_single_json")
        else "--dump-json"
    )
    args = [
        ytdlp_path,
        "--ignore-config",
        "--no-plugin-dirs",
        "--no-remote-components",
        "--encoding",
        DEFAULT_ENCODING,
        dump_option,
        "--no-warnings",
    ]

    if options:
        if options.get("extract_flat") is True:
            args.append("--flat-playlist")

        if options.get("noplaylist"):
            args.append("--no-playlist")

        if "format" in options:
            args.extend(["--format", options["format"]])

        if "format_sort" in options:
            args.extend(["--format-sort", options["format_sort"]])

        if "cookiefile" in options:
            args.extend(["--cookies", options["cookiefile"]])

        if "js_runtimes" in options:
            args.extend(["--js-runtimes", options["js_runtimes"]])

    args.extend(["--", url])
    return args
