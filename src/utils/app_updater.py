"""App self-update helpers using the GitHub Releases API."""

import os
import sys
import subprocess
import requests
from packaging import version
from packaging.version import InvalidVersion
from constants import (
    APP_RELEASE_API_URL,
    APP_UPDATE_ASSET_EXTENSION,
    APP_UPDATE_ASSET_PREFIX,
    APP_UPDATE_TEMP_ENV_VARS,
    APP_UPDATE_TEMP_FALLBACK_DIR,
    APP_VERSION,
    HTTP_API_TIMEOUT_SEC,
    HTTP_DOWNLOAD_CHUNK_SIZE,
    HTTP_DOWNLOAD_TIMEOUT_SEC,
    INNO_SETUP_INSTALL_ARGS,
    UPDATE_TEMP_FILENAME,
)
from utils.logger import log


# GitHub repository info.
GITHUB_API_URL = APP_RELEASE_API_URL


def update_temp_dir() -> str:
    """Return the temp directory used for downloaded app updates."""
    for env_var in APP_UPDATE_TEMP_ENV_VARS:
        temp_dir = os.environ.get(env_var)
        if temp_dir:
            return temp_dir
    return APP_UPDATE_TEMP_FALLBACK_DIR

def check_for_updates():
    """
    Check the latest version through the GitHub API.
    
    Returns:
        Tuple of update availability, latest version, and download URL; otherwise False, None, None.
    """
    try:
        log.info(f"앱 업데이트 확인 중: {GITHUB_API_URL}")
        
        # Call the GitHub API.
        response = requests.get(GITHUB_API_URL, timeout=HTTP_API_TIMEOUT_SEC)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').lstrip('v')  # 'v1.2.0' -> '1.2.0'
        
        if not latest_version:
            log.warning("GitHub API에서 버전 정보를 찾을 수 없습니다.")
            return False, None, None
        
        # Compare the current and latest versions.
        current_ver = APP_VERSION.lstrip('v')
        log.info(f"현재 버전: {current_ver}, 최신 버전: {latest_version}")
        
        if version.parse(latest_version) > version.parse(current_ver):
            # Update available: prefer Setup assets.
            assets = release_data.get('assets', [])
            download_url = None
            
            for asset in assets:
                name = asset['name']
                # Prefer the Setup file.
                if name.lower().startswith(APP_UPDATE_ASSET_PREFIX) and name.endswith(APP_UPDATE_ASSET_EXTENSION):
                    download_url = asset['browser_download_url']
                    break
            
            # If no Setup file exists, choose a regular exe file.
            if not download_url:
                for asset in assets:
                    if asset['name'].endswith(APP_UPDATE_ASSET_EXTENSION):
                        download_url = asset['browser_download_url']
                        break
            
            if download_url:
                log.info(f"업데이트 가능: {latest_version}, 다운로드 URL: {download_url}")
                return True, latest_version, download_url
            else:
                log.warning("GitHub Release에서 exe 파일을 찾을 수 없습니다.")
                return False, None, None
        else:
            # Already on the latest version.
            log.info("이미 최신 버전입니다.")
            return False, None, None
            
    except requests.exceptions.RequestException as e:
        log.error(f"GitHub API 호출 실패: {e}", exc_info=True)
        return False, None, None
    except (InvalidVersion, KeyError, TypeError, ValueError) as e:
        log.error(f"업데이트 확인 중 오류: {e}", exc_info=True)
        return False, None, None


def download_update(download_url, progress_callback=None):
    """
    Download the latest Setup file.
    
    Args:
        download_url: Download URL.
        progress_callback: Optional progress callback.
    
    Returns:
        Downloaded file path, or None.
    """
    try:
        log.info(f"업데이트 다운로드 시작: {download_url}")
        
        # Temporary file path.
        temp_dir = update_temp_dir()
        temp_file_path = os.path.join(temp_dir, UPDATE_TEMP_FILENAME)
        
        # Streaming download.
        response = requests.get(download_url, stream=True, timeout=HTTP_DOWNLOAD_TIMEOUT_SEC)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=HTTP_DOWNLOAD_CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress callback.
                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)
        
        log.info(f"업데이트 다운로드 완료: {temp_file_path}")
        return temp_file_path
        
    except (OSError, requests.exceptions.RequestException, ValueError) as e:
        log.error(f"업데이트 다운로드 실패: {e}", exc_info=True)
        return None


def apply_update(setup_exe_path):
    """
    Apply an update with the downloaded Inno Setup installer.
    
    Args:
        setup_exe_path: Setup installer path.
    
    Returns:
        True on success.
    """
    try:
        if not getattr(sys, 'frozen', False):
            log.warning("개발 환경에서는 업데이트를 적용할 수 없습니다.")
            return False
        
        if not os.path.exists(setup_exe_path):
            log.error(f"Setup 파일을 찾을 수 없습니다: {setup_exe_path}")
            return False
        
        log.info(f"Inno Setup 사일런트 설치 실행: {setup_exe_path}")
        
        # Run the Inno Setup installer in silent mode.
        # /SILENT: minimal UI showing progress only.
        # /SUPPRESSMSGBOXES: suppress message boxes.
        # /NORESTART: do not restart Windows.
        # /CLOSEAPPLICATIONS: close the running app automatically.
        subprocess.Popen(
            [setup_exe_path, *INNO_SETUP_INSTALL_ARGS],
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
        )
        
        log.info("Setup 실행 완료, 앱 종료 예정...")
        return True
        
    except (OSError, subprocess.SubprocessError) as e:
        log.error(f"업데이트 적용 실패: {e}", exc_info=True)
        return False
