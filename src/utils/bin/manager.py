"""
바이너리 관리 모듈 (yt-dlp.exe, ffmpeg.exe, qjs.exe)
- %APPDATA%\YTDownloader\bin에 바이너리 저장
- GitHub API를 통한 버전 확인 및 업데이트
- 다운로드 진행률 콜백 지원
"""
from typing import Optional, Tuple, Callable, Dict
from utils.logger import log
from utils.bin.release_info import ffmpeg_release_info, quickjs_release_info, ytdlp_release_info
from utils.bin.executable_install import download_and_install_executable_binary
from utils.bin.install import save_last_check
from utils.bin.ffmpeg_download import download_and_install_ffmpeg_zip
from utils.bin.ffmpeg_install import install_ffmpeg_from_zip
from utils.bin.release_fetch import check_latest_github_release
from utils.download_stream import download_file
from utils.bin.storage import (
    binary_path,
    get_bin_path,
    load_versions_file,
    save_versions_file,
    version_file_path,
)
from utils.bin.update_plan import (
    collect_available_updates,
    initial_update_results,
    needs_update_from_versions,
    should_check_after,
)
from utils.bin.operation_runner import run_binary_updates, run_initial_binary_downloads
from constants import (
    FFMPEG_ZIP_NAME_WIN,
    FFMPEG_EXE_INTERNAL_PATH,
    FFMPEG_EXE_INTERNAL_PATH_ROOT
)

# 바이너리 이름
YTDLP_BINARY = 'yt-dlp.exe'
FFMPEG_BINARY = 'ffmpeg.exe'
QUICKJS_BINARY = 'qjs.exe'

# GitHub API URLs
YTDLP_API_URL = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
FFMPEG_API_URL = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"
QUICKJS_API_URL = "https://api.github.com/repos/quickjs-ng/quickjs/releases/latest"

# QuickJS 다운로드 에셋 이름 (플랫폼별)
QUICKJS_ASSET_NAME = 'qjs-windows-x86_64.exe'

# 버전 파일명
VERSION_FILE = '.version.json'

# 업데이트 체크 주기 (시간)
UPDATE_CHECK_INTERVAL = 12  # 12시간마다 체크


def get_ytdlp_path() -> Optional[str]:
    """Return the managed yt-dlp executable path when present."""
    return binary_path(YTDLP_BINARY)


def get_ffmpeg_path() -> Optional[str]:
    """Return the managed ffmpeg executable path when present."""
    return binary_path(FFMPEG_BINARY)


def get_quickjs_path() -> Optional[str]:
    """Return the managed QuickJS executable path when present."""
    return binary_path(QUICKJS_BINARY)


def get_version_file_path() -> str:
    """Return the version metadata file path."""
    return version_file_path(VERSION_FILE)


def load_versions() -> Dict[str, object]:
    """Load managed binary version metadata."""
    return load_versions_file(VERSION_FILE)


def save_versions(versions: Dict[str, object]) -> bool:
    """Persist managed binary version metadata."""
    return save_versions_file(versions, VERSION_FILE)


def check_binaries_exist() -> bool:
    """
    yt-dlp와 ffmpeg가 모두 존재하는지 확인 (QuickJS는 선택적)

    Returns:
        True if both yt-dlp and ffmpeg exist, False otherwise
    """
    ytdlp_exists = get_ytdlp_path() is not None
    ffmpeg_exists = get_ffmpeg_path() is not None
    quickjs_exists = get_quickjs_path() is not None

    log.info(f"Binary check - yt-dlp: {ytdlp_exists}, ffmpeg: {ffmpeg_exists}, quickjs: {quickjs_exists}")
    return ytdlp_exists and ffmpeg_exists


def should_check_updates() -> bool:
    """Return whether update checks should run based on the saved timestamp."""
    versions = load_versions()
    last_check_str = versions.get('last_check')

    should_check = should_check_after(last_check_str, UPDATE_CHECK_INTERVAL)
    log.info(
        f"Update check - Last: {last_check_str}, "
        f"Interval hours: {UPDATE_CHECK_INTERVAL}, Should check: {should_check}"
    )
    return should_check


def check_ytdlp_latest_version() -> Tuple[Optional[str], Optional[str]]:
    """Check the latest yt-dlp release from GitHub."""
    return check_latest_github_release(
        YTDLP_API_URL,
        'yt-dlp',
        lambda data: ytdlp_release_info(data, YTDLP_BINARY),
        "yt-dlp.exe not found in release assets",
    )


def check_ffmpeg_latest_version() -> Tuple[Optional[str], Optional[str]]:
    """Check the latest FFmpeg release from GitHub."""
    return check_latest_github_release(
        FFMPEG_API_URL,
        'ffmpeg',
        lambda data: ffmpeg_release_info(data, FFMPEG_ZIP_NAME_WIN),
        f"ffmpeg asset ({FFMPEG_ZIP_NAME_WIN}) not found in release",
    )


def download_ytdlp(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install yt-dlp.exe."""
    version, url = check_ytdlp_latest_version()
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
    )


def download_ffmpeg(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install ffmpeg.exe from a ZIP release asset."""
    version, url = check_ffmpeg_latest_version()
    return download_and_install_ffmpeg_zip(
        version,
        url,
        FFMPEG_BINARY,
        (FFMPEG_EXE_INTERNAL_PATH, FFMPEG_EXE_INTERNAL_PATH_ROOT),
        get_bin_path,
        download_file,
        install_ffmpeg_from_zip,
        load_versions,
        save_versions,
        progress_callback,
        check_cancel,
    )


def check_quickjs_latest_version() -> Tuple[Optional[str], Optional[str]]:
    """Check the latest QuickJS release from GitHub."""
    return check_latest_github_release(
        QUICKJS_API_URL,
        'QuickJS',
        lambda data: quickjs_release_info(data, QUICKJS_ASSET_NAME),
        f"QuickJS asset ({QUICKJS_ASSET_NAME}) not found in release",
    )


def download_quickjs(
    progress_callback: Optional[Callable[[int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download and install QuickJS (qjs.exe)."""
    version, url = check_quickjs_latest_version()
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
    )


def needs_update(binary_name: str) -> bool:
    """Return whether a managed binary needs an update."""
    versions = load_versions()
    local_version = versions.get(binary_name)

    if binary_name == 'yt-dlp':
        latest_version, _ = check_ytdlp_latest_version()
    elif binary_name == 'ffmpeg':
        latest_version, _ = check_ffmpeg_latest_version()
    else:
        return False

    needs_update_flag = needs_update_from_versions(local_version, latest_version)
    log.info(
        f"{binary_name} - Local: {local_version}, "
        f"Latest: {latest_version}, Needs update: {needs_update_flag}"
    )
    return needs_update_flag


def check_updates_available() -> Dict[str, Dict[str, str]]:
    """Check which managed binaries have available updates."""
    versions = load_versions()
    latest_ytdlp, _ = check_ytdlp_latest_version()
    latest_ffmpeg, _ = check_ffmpeg_latest_version()
    return collect_available_updates(
        versions,
        {
            'yt-dlp': latest_ytdlp,
            'ffmpeg': latest_ffmpeg,
        },
    )


def download_initial_binaries(
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
    check_cancel: Optional[Callable[[], bool]] = None,
) -> bool:
    """Download initial managed binaries."""
    return run_initial_binary_downloads(
        (
            ('yt-dlp', download_ytdlp, "Failed to download yt-dlp", True),
            ('ffmpeg', download_ffmpeg, "Failed to download ffmpeg", True),
            (
                'quickjs',
                download_quickjs,
                "Failed to download QuickJS (optional, continuing)",
                False,
            ),
        ),
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
        ),
        initial_update_results(),
        updates_to_apply,
        needs_update,
        lambda: save_last_check(load_versions, save_versions),
        progress_callback,
        check_cancel,
    )