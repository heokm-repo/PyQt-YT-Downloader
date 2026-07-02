"""Executable binary download/install helpers."""

import os
from typing import Any, Callable, Mapping, Optional

from utils.bin.install import install_downloaded_binary, remove_if_exists
from utils.logger import log


DownloadFile = Callable[
    [str, str, Optional[Callable[[int, int], None]], Optional[Callable[[], bool]]],
    bool,
]


def download_and_install_executable_binary(
    binary_name: str,
    executable_name: str,
    display_name: str,
    version: Optional[str],
    url: Optional[str],
    missing_url_message: str,
    get_bin_path: Callable[[], str],
    download_file: DownloadFile,
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download one executable binary and install it into the bin directory."""
    if not url:
        log.error(missing_url_message)
        return False

    final_path = os.path.join(get_bin_path(), executable_name)
    temp_path = final_path + '.tmp'

    success = download_file(url, temp_path, progress_callback, check_cancel)
    if not success:
        remove_if_exists(temp_path)
        return False

    install_downloaded_binary(
        temp_path,
        final_path,
        binary_name,
        version,
        load_versions,
        save_versions,
    )
    log.info(f"{display_name} {version} installed successfully")
    return True