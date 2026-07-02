"""Parse yt-dlp progress output."""

import re
from typing import Optional


PROGRESS_PATTERN = re.compile(
    r"\[download\]\s+(?P<percent>[\d.]+)%\s+of\s+(?P<total>[\d.]+)(?P<total_unit>\w+)"
    r"(?:\s+at\s+(?P<speed>[\d.]+)(?P<speed_unit>\w+)/s)?"
    r"(?:\s+ETA\s+(?P<eta>[\d:]+))?"
)


def parse_progress(line: str) -> Optional[dict]:
    match = PROGRESS_PATTERN.search(line)
    if not match:
        return None

    percent = float(match.group("percent"))
    total_size = float(match.group("total"))
    total_unit = match.group("total_unit")
    speed_str = match.group("speed")
    speed_unit = match.group("speed_unit")
    eta_str = match.group("eta")

    total_bytes = convert_to_bytes(total_size, total_unit)
    downloaded_bytes = int(total_bytes * percent / 100)

    speed = None
    if speed_str and speed_unit:
        speed = convert_to_bytes(float(speed_str), speed_unit)

    eta = None
    if eta_str:
        eta = parse_eta(eta_str)

    return {
        "status": "downloading",
        "downloaded_bytes": downloaded_bytes,
        "total_bytes": total_bytes,
        "speed": speed,
        "eta": eta,
        "_percent_str": f"{percent}%",
        "_total_bytes_str": f"{total_size}{total_unit}",
        "_speed_str": f"{speed_str}{speed_unit}/s" if speed_str else None,
    }


def convert_to_bytes(size: float, unit: str) -> int:
    if "iB" in unit:
        unit = unit.replace("iB", "")
        multiplier = 1024
    else:
        unit = unit.replace("B", "")
        multiplier = 1000

    unit_map = {
        "K": multiplier,
        "M": multiplier ** 2,
        "G": multiplier ** 3,
        "T": multiplier ** 4,
    }

    return int(size * unit_map.get(unit, 1))


def parse_eta(eta_str: str) -> int:
    parts = eta_str.split(":")

    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0
