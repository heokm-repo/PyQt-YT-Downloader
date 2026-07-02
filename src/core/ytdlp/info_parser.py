"""Parse yt-dlp --dump-json output."""

import json
from typing import Any, Dict, Optional, Tuple

from utils.logger import log


def parse_info_output(stdout: str) -> Tuple[Optional[Dict[str, Any]], bool]:
    """Convert yt-dlp JSON stdout into the existing extract_info result shape."""
    text = (stdout or "").strip()
    if not text:
        return None, False

    lines = text.split("\n")
    if len(lines) == 1:
        return json.loads(lines[0]), True

    entries = []
    for line in lines:
        if not line.strip():
            continue

        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError as exc:
            log.debug(f"Skipping non-JSON yt-dlp output line: {exc}")

    if not entries:
        return None, False

    if len(entries) == 1:
        return entries[0], True

    return {"entries": entries, "_type": "playlist"}, True
