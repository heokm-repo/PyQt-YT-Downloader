"""
바이너리 관리 모듈 (yt-dlp.exe, ffmpeg.exe)
- %APPDATA%\YTDownloader\bin에 바이너리 저장
- GitHub API를 통한 버전 확인 및 업데이트
- 다운로드 진행률 콜백 지원
"""
import os
import sys
import json
import requests
import shutil
import tempfile
from typing import Optional, Tuple, Callable, Dict
from datetime import datetime, timedelta
from datetime import datetime, timedelta
from utils.logger import log
from constants import (
    FFMPEG_ZIP_NAME_WIN,
    FFMPEG_ZIP_NAME_LINUX,
    FFMPEG_EXE_INTERNAL_PATH,
    FFMPEG_EXE_INTERNAL_PATH_ROOT
)

# 바이너리 이름
YTDLP_BINARY = 'yt-dlp.exe' if sys.platform == 'win32' else 'yt-dlp'
FFMPEG_BINARY = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'

# GitHub API URLs
YTDLP_API_URL = "https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest"
FFMPEG_API_URL = "https://api.github.com/repos/BtbN/FFmpeg-Builds/releases/latest"

# 버전 파일명
VERSION_FILE = '.version.json'

# 업데이트 체크 주기 (시간)
UPDATE_CHECK_INTERVAL = 12  # 12시간마다 체크


def get_bin_path() -> str:
    """
    바이너리 저장 디렉토리 경로 반환
    Windows: %APPDATA%\YTDownloader\bin
    macOS: ~/Library/Application Support/YTDownloader/bin
    Linux: ~/.local/share/YTDownloader/bin
    """
    from utils.utils import get_user_data_path
    
    bin_path = os.path.join(get_user_data_path(), 'bin')
    
    # 디렉토리 생성
    if not os.path.exists(bin_path):
        try:
            os.makedirs(bin_path, exist_ok=True)
            log.info(f"Created bin directory: {bin_path}")
        except OSError as e:
            log.error(f"Failed to create bin directory: {e}")
            raise
    
    return bin_path


def get_ytdlp_path() -> Optional[str]:
    """yt-dlp 실행 파일 경로 반환"""
    path = os.path.join(get_bin_path(), YTDLP_BINARY)
    return path if os.path.exists(path) else None


def get_ffmpeg_path() -> Optional[str]:
    """ffmpeg 실행 파일 경로 반환"""
    path = os.path.join(get_bin_path(), FFMPEG_BINARY)
    return path if os.path.exists(path) else None


def get_version_file_path() -> str:
    """버전 정보 파일 경로 반환"""
    return os.path.join(get_bin_path(), VERSION_FILE)


def load_versions() -> Dict[str, any]:
    """
    버전 정보 파일 로드
    
    Returns:
        {
            "yt-dlp": "2024.01.30",
            "ffmpeg": "6.1",
            "last_check": "2024-01-30T11:00:00"
        }
    """
    version_file = get_version_file_path()
    
    if not os.path.exists(version_file):
        return {}
    
    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Failed to load version file: {e}")
        return {}


def save_versions(versions: Dict[str, any]) -> bool:
    """
    버전 정보 파일 저장
    
    Args:
        versions: 버전 정보 딕셔너리
    
    Returns:
        성공 여부
    """
    version_file = get_version_file_path()
    
    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            json.dump(versions, f, indent=2, ensure_ascii=False)
        return True
    except IOError as e:
        log.error(f"Failed to save version file: {e}")
        return False


def check_binaries_exist() -> bool:
    """
    yt-dlp와 ffmpeg가 모두 존재하는지 확인
    
    Returns:
        True if both exist, False otherwise
    """
    ytdlp_exists = get_ytdlp_path() is not None
    ffmpeg_exists = get_ffmpeg_path() is not None
    
    log.info(f"Binary check - yt-dlp: {ytdlp_exists}, ffmpeg: {ffmpeg_exists}")
    return ytdlp_exists and ffmpeg_exists


def should_check_updates() -> bool:
    """
    업데이트 체크가 필요한지 확인 (마지막 체크로부터 12시간 경과)
    
    Returns:
        True if should check, False otherwise
    """
    versions = load_versions()
    last_check_str = versions.get('last_check')
    
    if not last_check_str:
        return True
    
    try:
        last_check = datetime.fromisoformat(last_check_str)
        elapsed = datetime.now() - last_check
        
        should_check = elapsed > timedelta(hours=UPDATE_CHECK_INTERVAL)
        log.info(f"Update check - Last: {last_check}, Elapsed: {elapsed}, Should check: {should_check}")
        return should_check
    except (ValueError, TypeError) as e:
        log.error(f"Failed to parse last_check time: {e}")
        return True


def check_ytdlp_latest_version() -> Tuple[Optional[str], Optional[str]]:
    """
    GitHub API로 yt-dlp 최신 버전 확인
    
    Returns:
        (버전, 다운로드 URL) 또는 (None, None)
    """
    try:
        log.info(f"Checking yt-dlp latest version from {YTDLP_API_URL}")
        response = requests.get(YTDLP_API_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        version = data.get('tag_name', '').lstrip('v')  # "v2024.01.30" -> "2024.01.30"
        
        # Windows용 yt-dlp.exe 찾기
        for asset in data.get('assets', []):
            if asset['name'] == YTDLP_BINARY:
                download_url = asset['browser_download_url']
                log.info(f"Latest yt-dlp version: {version}, URL: {download_url}")
                return version, download_url
        
        log.warning("yt-dlp.exe not found in release assets")
        return None, None
        
    except requests.RequestException as e:
        log.error(f"Failed to check yt-dlp version: {e}")
        return None, None


def check_ffmpeg_latest_version() -> Tuple[Optional[str], Optional[str]]:
    """
    GitHub API로 ffmpeg 최신 버전 확인
    
    Returns:
        (버전, 다운로드 URL) 또는 (None, None)
    """
    try:
        log.info(f"Checking ffmpeg latest version from {FFMPEG_API_URL}")
        response = requests.get(FFMPEG_API_URL, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # BtbN/FFmpeg-Builds는 tag_name이 'latest'이므로 published_at 사용
        published_at = data.get('published_at', '')
        if published_at:
            # "2024-01-30T12:34:56Z" -> "2024.01.30"
            version = published_at[:10].replace('-', '.')
        else:
            version = data.get('tag_name', '').lstrip('v')
        
        # Windows용 ffmpeg 찾기 (일반적으로 ffmpeg-master-latest-win64-gpl.zip)
        # Windows용 ffmpeg 찾기 (일반적으로 ffmpeg-master-latest-win64-gpl.zip)
        target_name = FFMPEG_ZIP_NAME_WIN if sys.platform == 'win32' else FFMPEG_ZIP_NAME_LINUX
        
        for asset in data.get('assets', []):
            if target_name in asset['name']:
                download_url = asset['browser_download_url']
                log.info(f"Latest ffmpeg version: {version}, URL: {download_url}")
                return version, download_url
        
        log.warning(f"ffmpeg asset ({target_name}) not found in release")
        return None, None
        
    except requests.RequestException as e:
        log.error(f"Failed to check ffmpeg version: {e}")
        return None, None



def download_file(url: str, dest_path: str, progress_callback: Optional[Callable[[int, int], None]] = None, check_cancel: Optional[Callable[[], bool]] = None) -> bool:
    """
    파일 다운로드 (진행률 콜백 및 취소 지원)
    
    Args:
        url: 다운로드 URL
        dest_path: 저장 경로
        progress_callback: 진행률 콜백 (downloaded_bytes, total_bytes)
        check_cancel: 취소 여부 확인 콜백 (True 반환 시 취소)
    
    Returns:
        성공 여부
    """
    try:
        log.info(f"Downloading {url} to {dest_path}")
        
        if check_cancel and check_cancel():
            log.info("Download cancelled before start")
            return False

        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded_size = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
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


def download_ytdlp(progress_callback: Optional[Callable[[int, int], None]] = None, check_cancel: Optional[Callable[[], bool]] = None) -> bool:
    """
    yt-dlp.exe 다운로드
    
    Args:
        progress_callback: 진행률 콜백 (downloaded_bytes, total_bytes)
        check_cancel: 취소 여부 확인 콜백
    
    Returns:
        성공 여부
    """
    version, url = check_ytdlp_latest_version()
    
    if not url:
        log.error("Cannot get yt-dlp download URL")
        return False
    
    bin_path = get_bin_path()
    final_path = os.path.join(bin_path, YTDLP_BINARY)
    temp_path = final_path + '.tmp'
    
    # 임시 파일에 다운로드
    success = download_file(url, temp_path, progress_callback, check_cancel)
    
    if success:
        # 기존 파일이 있으면 삭제
        if os.path.exists(final_path):
            os.remove(final_path)
        
        # 임시 파일을 최종 위치로 이동
        shutil.move(temp_path, final_path)
        
        # 버전 정보 업데이트
        versions = load_versions()
        versions['yt-dlp'] = version
        versions['last_check'] = datetime.now().isoformat()
        save_versions(versions)
        
        log.info(f"yt-dlp {version} installed successfully")
        return True
    else:
        # 실패 시 임시 파일 삭제
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False


def download_ffmpeg(progress_callback: Optional[Callable[[int, int], None]] = None, check_cancel: Optional[Callable[[], bool]] = None) -> bool:
    """
    ffmpeg.exe 다운로드 (ZIP 압축 해제 포함)
    
    Args:
        progress_callback: 진행률 콜백 (downloaded_bytes, total_bytes)
        check_cancel: 취소 여부 확인 콜백
    
    Returns:
        성공 여부
    """
    version, url = check_ffmpeg_latest_version()
    
    if not url:
        log.error("Cannot get ffmpeg download URL")
        return False
    
    bin_path = get_bin_path()
    
    # 임시 ZIP 파일 다운로드
    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        temp_zip_path = tmp.name
    
    try:
        # ZIP 다운로드
        success = download_file(url, temp_zip_path, progress_callback, check_cancel)
        
        if not success:
            return False
        
        if check_cancel and check_cancel():
            return False
            
        # ZIP 압축 해제
        log.info(f"Extracting ffmpeg from {temp_zip_path}")
        import zipfile
        
        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
            # ffmpeg.exe 찾기 (보통 bin/ffmpeg.exe 경로에 있음)
            for file_info in zip_ref.filelist:
                if file_info.filename.endswith(FFMPEG_EXE_INTERNAL_PATH) or file_info.filename.endswith(FFMPEG_EXE_INTERNAL_PATH_ROOT):
                    # ffmpeg.exe 추출
                    with zip_ref.open(file_info) as source:
                        final_path = os.path.join(bin_path, FFMPEG_BINARY)
                        with open(final_path, 'wb') as target:
                            shutil.copyfileobj(source, target)
                    
                    log.info(f"ffmpeg extracted to {final_path}")
                    
                    # 버전 정보 업데이트
                    versions = load_versions()
                    versions['ffmpeg'] = version
                    versions['last_check'] = datetime.now().isoformat()
                    save_versions(versions)
                    
                    return True
        
        log.error("ffmpeg.exe not found in zip archive")
        return False
        
    except Exception as e:
        log.error(f"Failed to extract ffmpeg: {e}")
        return False
    finally:
        # 임시 ZIP 파일 삭제
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)



def needs_update(binary_name: str) -> bool:
    """
    특정 바이너리의 업데이트 필요 여부 확인
    
    Args:
        binary_name: 'yt-dlp' 또는 'ffmpeg'
    
    Returns:
        True if update needed, False otherwise
    """
    versions = load_versions()
    local_version = versions.get(binary_name)
    
    if not local_version:
        return True
    
    # GitHub에서 최신 버전 확인
    if binary_name == 'yt-dlp':
        latest_version, _ = check_ytdlp_latest_version()
    elif binary_name == 'ffmpeg':
        latest_version, _ = check_ffmpeg_latest_version()
    else:
        return False
    
    if not latest_version:
        return False
    
    needs_update_flag = local_version != latest_version
    log.info(f"{binary_name} - Local: {local_version}, Latest: {latest_version}, Needs update: {needs_update_flag}")
    
    return needs_update_flag


def check_updates_available() -> Dict[str, Dict[str, str]]:
    """
    업데이트 가능한 바이너리 확인
    
    Returns:
        {
            'yt-dlp': {'current': '2024.01.01', 'latest': '2024.01.30'},
            'ffmpeg': {'current': '6.0', 'latest': '6.1'}
        }
        업데이트가 없으면 빈 딕셔너리 반환
    """
    updates = {}
    versions = load_versions()
    
    # yt-dlp 체크
    local_ytdlp = versions.get('yt-dlp')
    latest_ytdlp, _ = check_ytdlp_latest_version()
    
    if local_ytdlp and latest_ytdlp and local_ytdlp != latest_ytdlp:
        updates['yt-dlp'] = {
            'current': local_ytdlp,
            'latest': latest_ytdlp
        }
    
    # ffmpeg 체크
    local_ffmpeg = versions.get('ffmpeg')
    latest_ffmpeg, _ = check_ffmpeg_latest_version()
    
    if local_ffmpeg and latest_ffmpeg and local_ffmpeg != latest_ffmpeg:
        updates['ffmpeg'] = {
            'current': local_ffmpeg,
            'latest': latest_ffmpeg
        }
    
    return updates


def download_initial_binaries(progress_callback: Optional[Callable[[str, int, int], None]] = None, check_cancel: Optional[Callable[[], bool]] = None) -> bool:
    """
    초기 바이너리 다운로드 (yt-dlp + ffmpeg)
    
    Args:
        progress_callback: 진행률 콜백 (binary_name, downloaded_bytes, total_bytes)
        check_cancel: 취소 여부 확인 콜백
    
    Returns:
        성공 여부
    """
    log.info("Starting initial binary download")
    
    # yt-dlp 다운로드
    def ytdlp_progress(downloaded, total):
        if progress_callback:
            progress_callback('yt-dlp', downloaded, total)
    
    if check_cancel and check_cancel():
        return False

    if not download_ytdlp(ytdlp_progress, check_cancel):
        log.error("Failed to download yt-dlp")
        return False
    
    if check_cancel and check_cancel():
        return False
    
    # ffmpeg 다운로드
    def ffmpeg_progress(downloaded, total):
        if progress_callback:
            progress_callback('ffmpeg', downloaded, total)
    
    if not download_ffmpeg(ffmpeg_progress, check_cancel):
        log.error("Failed to download ffmpeg")
        return False
    
    log.info("Initial binary download completed successfully")
    return True


def update_binaries(progress_callback: Optional[Callable[[str, int, int], None]] = None, updates_to_apply: Optional[Dict[str, Dict[str, str]]] = None, check_cancel: Optional[Callable[[], bool]] = None) -> Dict[str, bool]:
    """
    바이너리 업데이트 (필요한 것만)
    
    Args:
        progress_callback: 진행률 콜백 (binary_name, downloaded_bytes, total_bytes)
        updates_to_apply: 업데이트할 바이너리 목록 (check_updates_available 결과)
                          None이면 모든 바이너리 체크
        check_cancel: 취소 여부 확인 콜백
    
    Returns:
        {"yt-dlp": True/False, "ffmpeg": True/False}
    """
    results = {
        'yt-dlp': False,
        'ffmpeg': False
    }
    
    log.info("Checking for binary updates")
    
    if check_cancel and check_cancel():
        return results

    # updates_to_apply가 지정되지 않으면 모든 바이너리 체크 (기존 동작)
    if updates_to_apply is None:
        binaries_to_check = ['yt-dlp', 'ffmpeg']
    else:
        # updates_to_apply에 있는 것만 업데이트
        binaries_to_check = list(updates_to_apply.keys())
        log.info(f"Updating only: {binaries_to_check}")
    
    # yt-dlp 업데이트
    if 'yt-dlp' in binaries_to_check and needs_update('yt-dlp'):
        log.info("Updating yt-dlp...")
        def ytdlp_progress(downloaded, total):
            if progress_callback:
                progress_callback('yt-dlp', downloaded, total)
        
        results['yt-dlp'] = download_ytdlp(ytdlp_progress, check_cancel)
    else:
        log.info("yt-dlp is up to date or not in update list")
        results['yt-dlp'] = True
    
    if check_cancel and check_cancel():
        return results
    
    # ffmpeg 업데이트
    if 'ffmpeg' in binaries_to_check and needs_update('ffmpeg'):
        log.info("Updating ffmpeg...")
        def ffmpeg_progress(downloaded, total):
            if progress_callback:
                progress_callback('ffmpeg', downloaded, total)
        
        results['ffmpeg'] = download_ffmpeg(ffmpeg_progress, check_cancel)
    else:
        log.info("ffmpeg is up to date or not in update list")
        results['ffmpeg'] = True
    
    # 업데이트 체크 시간 갱신 (성공한 경우에만?)
    # 취소되었어도 성공한 부분은 있을 수 있으므로 버전 파일 저장은 개별 함수에서 처리됨
    # 여기서는 last_check만 갱신
    if not (check_cancel and check_cancel()):
        versions = load_versions()
        versions['last_check'] = datetime.now().isoformat()
        save_versions(versions)
    
    return results
