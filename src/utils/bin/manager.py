"""Managed binary helpers for yt-dlp.exe, FFmpeg tools, and qjs.exe."""
from typing import Callable, Dict, Mapping, Optional, Sequence, Tuple
from utils.logger import log
from utils.bin.release_info import ffmpeg_release_info, quickjs_release_info, ytdlp_release_info
from utils.bin.executable_install import download_and_install_executable_binary
from utils.bin.ffmpeg_download import download_and_install_ffmpeg_zip
from utils.bin.ffmpeg_install import install_ffmpeg_from_zip
from utils.bin.release_fetch import (
    check_latest_github_release,
    check_latest_github_release_strict,
)
from utils.download_stream import download_file
from utils.bin.storage import (
    binary_path,
    get_bin_path,
    load_versions_file,
    save_versions_file,
)
from utils.bin.update_plan import (
    collect_available_updates,
    initial_update_results,
    needs_update_from_versions,
)
from utils.bin.operation_runner import run_binary_updates, run_initial_binary_downloads
from constants import (
    BIN_VERSION_FILENAME,
    FFMPEG_BINARY,
    FFPROBE_BINARY,
    FFMPEG_EXE_INTERNAL_PATH,
    FFMPEG_EXE_INTERNAL_PATH_ROOT,
    FFPROBE_EXE_INTERNAL_PATH,
    FFPROBE_EXE_INTERNAL_PATH_ROOT,
    FFMPEG_RELEASE_API_URL,
    FFMPEG_ZIP_NAME_WIN,
    QUICKJS_ASSET_NAME,
    QUICKJS_BINARY,
    QUICKJS_RELEASE_API_URL,
    YTDLP_BINARY,
    YTDLP_RELEASE_API_URL,
)

YTDLP_API_URL = YTDLP_RELEASE_API_URL
FFMPEG_API_URL = FFMPEG_RELEASE_API_URL
QUICKJS_API_URL = QUICKJS_RELEASE_API_URL
VERSION_FILE = BIN_VERSION_FILENAME
BINARY_DOWNLOAD_ORDER = ("yt-dlp", "ffmpeg", "quickjs")

def get_ytdlp_path() -> Optional[str]:
    """Return the managed yt-dlp executable path when present."""
    return binary_path(YTDLP_BINARY)


def get_ffmpeg_path() -> Optional[str]:
    """Return the managed ffmpeg executable path when present."""
    return binary_path(FFMPEG_BINARY)

def get_ffprobe_path() -> Optional[str]:
    """Return the managed ffprobe executable path when present."""
    return binary_path(FFPROBE_BINARY)


def get_quickjs_path() -> Optional[str]:
    """Return the managed QuickJS executable path when present."""
    return binary_path(QUICKJS_BINARY)


def check_binary_presence() -> Dict[str, bool]:
    """Return presence state for every required external executable."""
    return {
        "yt-dlp": get_ytdlp_path() is not None,
        "ffmpeg": get_ffmpeg_path() is not None,
        "ffprobe": get_ffprobe_path() is not None,
        "quickjs": get_quickjs_path() is not None,
    }


def missing_binary_downloads(
    presence: Mapping[str, bool],
) -> tuple[str, ...]:
    """Return the smallest managed downloads needed to repair binary presence."""
    missing: list[str] = []
    if not presence.get("yt-dlp", False):
        missing.append("yt-dlp")
    if (
        not presence.get("ffmpeg", False)
        or not presence.get("ffprobe", False)
    ):
        # FFmpeg and ffprobe are installed together from one release archive.
        missing.append("ffmpeg")
    if not presence.get("quickjs", False):
        missing.append("quickjs")
    return tuple(missing)


def load_versions() -> Dict[str, object]:
    """Load managed binary version metadata."""
    return load_versions_file(VERSION_FILE)


def save_versions(versions: Dict[str, object]) -> bool:
    """Persist managed binary version metadata."""
    return save_versions_file(versions, VERSION_FILE)


def check_binaries_exist() -> bool:
    """
    Return whether all required managed binaries exist.

    Returns:
        True if yt-dlp, ffmpeg, ffprobe, and QuickJS exist, False otherwise.
    """
    presence = check_binary_presence()
    log.info(
        "Binary check - yt-dlp: %s, ffmpeg: %s, ffprobe: %s, quickjs: %s",
        presence["yt-dlp"],
        presence["ffmpeg"],
        presence["ffprobe"],
        presence["quickjs"],
    )
    return all(presence.values())


def _check_ytdlp_release(
    release_checker: Callable,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    return release_checker(
        YTDLP_API_URL,
        'yt-dlp',
        lambda data: ytdlp_release_info(data, YTDLP_BINARY),
        "yt-dlp.exe not found in release assets",
    )


def _check_ffmpeg_release(
    release_checker: Callable,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    return release_checker(
        FFMPEG_API_URL,
        'ffmpeg',
        lambda data: ffmpeg_release_info(data, FFMPEG_ZIP_NAME_WIN),
        f"ffmpeg asset ({FFMPEG_ZIP_NAME_WIN}) not found in release",
    )


def check_ytdlp_latest_version() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Check the latest yt-dlp release from GitHub."""
    return _check_ytdlp_release(check_latest_github_release)


def check_ffmpeg_latest_version() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Check the latest FFmpeg release from GitHub."""
    return _check_ffmpeg_release(check_latest_github_release)


def download_ytdlp(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install yt-dlp.exe."""
    version, url, digest = check_ytdlp_latest_version()
    return download_and_install_executable_binary(
        'yt-dlp',
        YTDLP_BINARY,
        'yt-dlp',
        version,
        url,
        "Cannot get yt-dlp download URL",
        get_bin_path,
        download_file,
        load_versions,
        save_versions,
        progress_callback,
        check_cancel,
        expected_digest=digest,
    )


def download_ffmpeg(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install ffmpeg.exe from a ZIP release asset."""
    version, url, digest = check_ffmpeg_latest_version()
    return download_and_install_ffmpeg_zip(
        version,
        url,
        FFMPEG_BINARY,
        FFPROBE_BINARY,
        (FFMPEG_EXE_INTERNAL_PATH, FFMPEG_EXE_INTERNAL_PATH_ROOT),
        (FFPROBE_EXE_INTERNAL_PATH, FFPROBE_EXE_INTERNAL_PATH_ROOT),
        get_bin_path,
        download_file,
        install_ffmpeg_from_zip,
        load_versions,
        save_versions,
        progress_callback,
        check_cancel,
        expected_digest=digest,
    )


def _check_quickjs_release(
    release_checker: Callable,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    return release_checker(
        QUICKJS_API_URL,
        'QuickJS',
        lambda data: quickjs_release_info(data, QUICKJS_ASSET_NAME),
        f"QuickJS asset ({QUICKJS_ASSET_NAME}) not found in release",
    )


def check_quickjs_latest_version() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Check the latest QuickJS release from GitHub."""
    return _check_quickjs_release(check_latest_github_release)


def download_quickjs(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install QuickJS (qjs.exe)."""
    version, url, digest = check_quickjs_latest_version()
    return download_and_install_executable_binary(
        'quickjs',
        QUICKJS_BINARY,
        'QuickJS',
        version,
        url,
        "Cannot get QuickJS download URL",
        get_bin_path,
        download_file,
        load_versions,
        save_versions,
        progress_callback,
        check_cancel,
        expected_digest=digest,
    )


def needs_update(binary_name: str) -> bool:
    """Return whether a managed binary needs an update."""
    versions = load_versions()
    local_version = versions.get(binary_name)

    if binary_name == 'yt-dlp':
        latest_version, _, _ = check_ytdlp_latest_version()
    elif binary_name == 'ffmpeg':
        latest_version, _, _ = check_ffmpeg_latest_version()
    elif binary_name == 'quickjs':
        latest_version, _, _ = check_quickjs_latest_version()
    else:
        return False

    needs_update_flag = needs_update_from_versions(local_version, latest_version)
    log.info(
        f"{binary_name} - Local: {local_version}, "
        f"Latest: {latest_version}, Needs update: {needs_update_flag}"
    )
    return needs_update_flag




def check_updates_available_strict() -> Dict[str, Dict[str, str]]:
    """Check binary updates, raising if any trusted release check fails."""
    versions = load_versions()
    latest_ytdlp, _, _ = _check_ytdlp_release(
        check_latest_github_release_strict
    )
    latest_ffmpeg, _, _ = _check_ffmpeg_release(
        check_latest_github_release_strict
    )
    latest_quickjs, _, _ = _check_quickjs_release(
        check_latest_github_release_strict
    )
    return collect_available_updates(
        versions,
        {
            'yt-dlp': latest_ytdlp,
            'ffmpeg': latest_ffmpeg,
            'quickjs': latest_quickjs,
        },
    )


def download_initial_binaries(
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
    binary_names: Optional[Sequence[str]] = None,
) -> bool:
    """Download the selected required binaries, or every binary on first launch."""
    requested = tuple(
        BINARY_DOWNLOAD_ORDER if binary_names is None else binary_names
    )
    unknown = sorted(set(requested).difference(BINARY_DOWNLOAD_ORDER))
    if unknown:
        log.error(f"Unknown managed binaries requested: {', '.join(unknown)}")
        return False

    specs = {
        'yt-dlp': ('yt-dlp', download_ytdlp, "Failed to download yt-dlp"),
        'ffmpeg': ('ffmpeg', download_ffmpeg, "Failed to download ffmpeg"),
        'quickjs': ('quickjs', download_quickjs, "Failed to download QuickJS"),
    }
    return run_initial_binary_downloads(
        tuple(specs[name] for name in BINARY_DOWNLOAD_ORDER if name in requested),
        progress_callback,
        check_cancel,
    )


def update_binaries(
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    updates_to_apply: Optional[Dict[str, Dict[str, str]]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> Dict[str, bool]:
    """Update managed binaries when needed."""
    return run_binary_updates(
        (
            ('yt-dlp', download_ytdlp),
            ('ffmpeg', download_ffmpeg),
            ('quickjs', download_quickjs),
        ),
        initial_update_results(),
        updates_to_apply,
        needs_update,
        progress_callback,
        check_cancel,
    )
