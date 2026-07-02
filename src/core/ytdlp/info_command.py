"""Build yt-dlp commands for metadata extraction."""

from typing import Any, Dict, List, Optional


def build_extract_info_command(
    ytdlp_path: str,
    url: str,
    options: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Convert extract_info options into yt-dlp CLI arguments."""
    args = [ytdlp_path, "--dump-json", "--no-warnings"]

    if options:
        if options.get("extract_flat") is True:
            args.append("--flat-playlist")

        if options.get("noplaylist"):
            args.append("--no-playlist")

        if "format" in options:
            args.extend(["--format", options["format"]])

        if "cookiefile" in options:
            args.extend(["--cookies", options["cookiefile"]])

        if "js_runtimes" in options:
            args.extend(["--js-runtimes", options["js_runtimes"]])

    args.append(url)
    return args
