"""Streaming file download helpers."""

import os
from typing import Callable, NamedTuple, Optional

import requests

from constants import HTTP_DOWNLOAD_CHUNK_SIZE, HTTP_DOWNLOAD_TIMEOUT_SEC
from utils.logger import log
from utils.url_security import redact_url_for_log


class DownloadCancelled(RuntimeError):
    def __init__(self, started=False):
        super().__init__('Download cancelled')
        self.started = started


class TransferResult(NamedTuple):
    downloaded: int
    total: int


def transfer_to_file(url, dest_path, progress_callback=None, check_cancel=None):
    """Own one response/file; leave cleanup and exception policy to adapters.

    Byte notifications remain lossless for known positive Content-Length.
    Cancellation is checked independently, including empty chunks and EOF.
    Blocking socket reads retain the existing HTTP timeout.
    """
    if check_cancel and check_cancel():
        raise DownloadCancelled()
    response = requests.get(url, stream=True, timeout=HTTP_DOWNLOAD_TIMEOUT_SEC)
    try:
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        with open(dest_path, 'wb') as stream:
            for chunk in response.iter_content(chunk_size=HTTP_DOWNLOAD_CHUNK_SIZE):
                if check_cancel and check_cancel():
                    raise DownloadCancelled(started=True)
                if chunk:
                    stream.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded, total)
            if check_cancel and check_cancel():
                raise DownloadCancelled(started=True)
        return TransferResult(downloaded, total)
    finally:
        response.close()


def download_file(
    url: str,
    dest_path: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download a file with optional progress and cancellation callbacks."""
    try:
        log.info(f"Downloading {redact_url_for_log(url)} to {dest_path}")

        transfer_to_file(url, dest_path, progress_callback, check_cancel)
        log.info(f"Download completed: {dest_path}")
        return True

    except DownloadCancelled as exc:
        log.info('Download cancelled')
        try:
            if exc.started and os.path.exists(dest_path):
                os.remove(dest_path)
        except OSError as error:
            log.error(f'File cleanup failed: {error}')
        return False
    except requests.RequestException as e:
        log.error(f"Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False
    except IOError as e:
        log.error(f"File write failed: {e}")
        return False
