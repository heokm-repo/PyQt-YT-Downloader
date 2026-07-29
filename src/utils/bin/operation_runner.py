"""Operation runners for binary download and update workflows."""

from typing import Any, Callable, Mapping, Optional, Sequence

from utils.bin.update_plan import scoped_progress_callback, selected_update_binaries
from utils.logger import log


BinaryProgress = Callable[[int, int], None]
NamedProgress = Callable[[str, int, int], None]
CancelCheck = Callable[[], bool]
BinaryDownloader = Callable[[Optional[BinaryProgress], Optional[CancelCheck]], bool]
NeedsUpdate = Callable[[str], bool]
InitialDownloadSpec = tuple[str, BinaryDownloader, str]
UpdateSpec = tuple[str, BinaryDownloader]


def download_initial_binary(
    binary_name: str,
    downloader: BinaryDownloader,
    progress_callback: Optional[NamedProgress],
    check_cancel: Optional[CancelCheck],
    failure_message: str,
) -> bool:
    """Download one required initial binary."""
    success = downloader(
        scoped_progress_callback(binary_name, progress_callback),
        check_cancel,
    )
    if success:
        return True

    log.error(failure_message)
    return False


def run_initial_binary_downloads(
    specs: Sequence[InitialDownloadSpec],
    progress_callback: Optional[NamedProgress],
    check_cancel: Optional[CancelCheck],
) -> bool:
    """Download initial binaries in order, stopping on required failures."""
    log.info("Starting initial binary download")

    for binary_name, downloader, failure_message in specs:
        if check_cancel and check_cancel():
            return False

        if not download_initial_binary(
            binary_name,
            downloader,
            progress_callback,
            check_cancel,
            failure_message,
        ):
            return False

    log.info("Initial binary download completed successfully")
    return True


def update_binary_if_needed(
    binary_name: str,
    downloader: BinaryDownloader,
    binaries_to_check: Sequence[str],
    needs_update: NeedsUpdate,
    progress_callback: Optional[NamedProgress],
    check_cancel: Optional[CancelCheck],
) -> bool:
    """Update one binary when it is selected and stale."""
    if binary_name not in binaries_to_check or not needs_update(binary_name):
        log.info(f"{binary_name} is up to date or not in update list")
        return True

    log.info(f"Updating {binary_name}...")
    return downloader(
        scoped_progress_callback(binary_name, progress_callback),
        check_cancel,
    )


def run_binary_updates(
    specs: Sequence[UpdateSpec],
    initial_results: Mapping[str, bool],
    updates_to_apply: Optional[Mapping[str, Any]],
    needs_update: NeedsUpdate,
    progress_callback: Optional[NamedProgress],
    check_cancel: Optional[CancelCheck],
) -> dict[str, bool]:
    """Update the selected managed binaries."""
    results = dict(initial_results)
    log.info("Checking for binary updates")

    if check_cancel and check_cancel():
        return results

    binaries_to_check = selected_update_binaries(updates_to_apply)
    if updates_to_apply is not None:
        log.info(f"Updating only: {binaries_to_check}")

    last_index = len(specs) - 1
    for index, (binary_name, downloader) in enumerate(specs):
        results[binary_name] = update_binary_if_needed(
            binary_name,
            downloader,
            binaries_to_check,
            needs_update,
            progress_callback,
            check_cancel,
        )

        if index != last_index and check_cancel and check_cancel():
            return results

    return results
