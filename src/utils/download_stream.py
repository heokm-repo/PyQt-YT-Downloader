"""Streaming file download helpers."""

import os
from typing import Callable, Optional

import requests

from constants import HTTP_DOWNLOAD_CHUNK_SIZE, HTTP_DOWNLOAD_TIMEOUT_SEC
from utils.logger import log
from utils.url_security import redact_url_for_log


def download_file(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download a file with optional progress and cancellation callbacks."""
    try:
        log.info(f"Downloading {redact_url_for_log(url)} to {dest_path}")

        if check_cancel and check_cancel():
            log.info("Download cancelled before start")
            return False

        response = requests.get(url, stream=True, timeout=HTTP_DOWNLOAD_TIMEOUT_SEC)
        response.raise_for_status()

        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0

        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=HTTP_DOWNLOAD_CHUNK_SIZE):
                if check_cancel and check_cancel():
                    log.info("Download cancelled during transfer")
                    f.close()
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    return False

                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)

                    if progress_callback and total_size > 0:
                        progress_callback(downloaded_size, total_size)

        log.info(f"Download completed: {dest_path}")
        return True

    except requests.RequestException as e:
        log.error(f"Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False
    except IOError as e:
        log.error(f"File write failed: {e}")
        return False
