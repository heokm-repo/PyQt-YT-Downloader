"""FFmpeg ZIP download/install workflow helpers."""

import os
import tempfile
import zipfile
from typing import Any, Callable, Mapping, Optional

from utils.integrity import verify_sha256
from utils.logger import log


BinaryProgress = Callable[[int, int], None]
CancelCheck = Callable[[], bool]
DownloadFile = Callable[[str, str, Optional[BinaryProgress], Optional[CancelCheck]], bool]
InstallFfmpeg = Callable[
    [
        str,
        str,
        str,
        tuple[str, ...],
        Callable[[], Mapping[str, Any]],
        Callable[[dict[str, Any]], bool],
    ],
    bool,
]


def download_and_install_ffmpeg_zip(
    version: Optional[str],
    url: Optional[str],
    executable_name: str,
    member_suffixes: tuple[str, ...],
    get_bin_path: Callable[[], str],
    download_file: DownloadFile,
    install_ffmpeg_from_zip: InstallFfmpeg,
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
    progress_callback: Optional[BinaryProgress] = None,
    check_cancel: Optional[CancelCheck] = None,
    expected_digest: Optional[str] = None,
) -> bool:
    """Download an FFmpeg ZIP archive and install ffmpeg from it."""
    if not url:
        log.error("Cannot get ffmpeg download URL")
        return False

    bin_path = get_bin_path()
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        temp_zip_path = tmp.name

    try:
        success = download_file(url, temp_zip_path, progress_callback, check_cancel)
        if not success:
            return False

        if check_cancel and check_cancel():
            return False

        if not verify_sha256(temp_zip_path, expected_digest):
            return False

        final_path = os.path.join(bin_path, executable_name)
        log.info(f"Extracting ffmpeg from {temp_zip_path}")
        return install_ffmpeg_from_zip(
            temp_zip_path,
            final_path,
            version,
            member_suffixes,
            load_versions,
            save_versions,
        )

    except (OSError, zipfile.BadZipFile) as e:
        log.error(f"Failed to extract ffmpeg: {e}", exc_info=True)
        return False
    finally:
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
