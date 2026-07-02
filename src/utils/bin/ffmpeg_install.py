"""FFmpeg ZIP install helpers for managed binary downloads."""

from typing import Any, Callable, Mapping

from utils.bin.archive import extract_zip_member_ending_with
from utils.bin.install import save_binary_version
from utils.logger import log


def install_ffmpeg_from_zip(
    zip_path: str,
    final_path: str,
    version: str,
    member_suffixes: tuple[str, ...],
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
) -> bool:
    """Extract ffmpeg from a ZIP archive and persist its version."""
    extracted = extract_zip_member_ending_with(zip_path, final_path, member_suffixes)
    if not extracted:
        log.error("ffmpeg.exe not found in zip archive")
        return False

    log.info(f"ffmpeg extracted to {final_path}")
    return save_binary_version('ffmpeg', version, load_versions, save_versions)