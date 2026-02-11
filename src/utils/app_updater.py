"""
앱 자체 업데이트 기능 모듈
GitHub Releases API를 통해 최신 버전 확인 및 다운로드
"""

import os
import sys
import subprocess
import requests
from packaging import version
from constants import APP_VERSION, GITHUB_REPO_OWNER, GITHUB_REPO_NAME, UPDATE_TEMP_FILENAME, UPDATE_BATCH_FILENAME, BATCH_ENCODING
from utils.logger import log


# GitHub 저장소 정보
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"


def check_for_updates():
    """
    GitHub API를 통해 최신 버전 확인
    
    Returns:
        tuple: (업데이트 가능 여부, 최신 버전, 다운로드 URL) 또는 (False, None, None)
    """
    try:
        log.info(f"앱 업데이트 확인 중: {GITHUB_API_URL}")
        
        # GitHub API 호출
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()
        
        release_data = response.json()
        latest_version = release_data.get('tag_name', '').lstrip('v')  # 'v1.2.0' -> '1.2.0'
        
        if not latest_version:
            log.warning("GitHub API에서 버전 정보를 찾을 수 없습니다.")
            return False, None, None
        
        # 현재 버전과 최신 버전 비교
        current_ver = APP_VERSION.lstrip('v')
        log.info(f"현재 버전: {current_ver}, 최신 버전: {latest_version}")
        
        if version.parse(latest_version) > version.parse(current_ver):
            # 업데이트 가능
            # assets에서 exe 파일 찾기
            assets = release_data.get('assets', [])
            download_url = None
            
            for asset in assets:
                if asset['name'].endswith('.exe'):
                    download_url = asset['browser_download_url']
                    break
            
            if download_url:
                log.info(f"업데이트 가능: {latest_version}, 다운로드 URL: {download_url}")
                return True, latest_version, download_url
            else:
                log.warning("GitHub Release에서 exe 파일을 찾을 수 없습니다.")
                return False, None, None
        else:
            # 이미 최신 버전
            log.info("이미 최신 버전입니다.")
            return False, None, None
            
    except requests.exceptions.RequestException as e:
        log.error(f"GitHub API 호출 실패: {e}", exc_info=True)
        return False, None, None
    except Exception as e:
        log.error(f"업데이트 확인 중 오류: {e}", exc_info=True)
        return False, None, None


def download_update(download_url, progress_callback=None):
    """
    최신 버전 exe 다운로드
    
    Args:
        download_url: 다운로드 URL
        progress_callback: 진행 상황 콜백 함수 (optional)
    
    Returns:
        str: 다운로드된 파일 경로 또는 None
    """
    try:
        log.info(f"업데이트 다운로드 시작: {download_url}")
        
        # 임시 파일 경로
        temp_dir = os.environ.get('TEMP', os.environ.get('TMP', '/tmp'))
        temp_file_path = os.path.join(temp_dir, UPDATE_TEMP_FILENAME)
        
        # 스트리밍 다운로드
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(temp_file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # 진행 상황 콜백
                    if progress_callback and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        progress_callback(progress)
        
        log.info(f"업데이트 다운로드 완료: {temp_file_path}")
        return temp_file_path
        
    except Exception as e:
        log.error(f"업데이트 다운로드 실패: {e}", exc_info=True)
        return None


def apply_update(new_exe_path):
    """
    다운로드한 exe로 업데이트 적용
    
    Args:
        new_exe_path: 새 exe 파일 경로
    
    Returns:
        bool: 성공 여부
    """
    try:
        if not getattr(sys, 'frozen', False):
            log.warning("개발 환경에서는 업데이트를 적용할 수 없습니다.")
            return False
        
        current_exe = sys.executable
        exe_dir = os.path.dirname(current_exe)
        bat_path = os.path.join(exe_dir, UPDATE_BATCH_FILENAME)
        
        # update.bat 스크립트 생성
        bat_content = f"""@echo off
echo YT Downloader 업데이트 중...

REM 2초 대기 (현재 exe 완전 종료 대기)
timeout /t 2 /nobreak >nul

REM 기존 exe 백업
if exist "{current_exe}.bak" (
    del /f /q "{current_exe}.bak"
)
move /y "{current_exe}" "{current_exe}.bak"

REM 새 exe 복사
move /y "{new_exe_path}" "{current_exe}"

REM 업데이트된 앱 재실행
start "" "{current_exe}"

REM 백업 파일 삭제
del /f /q "{current_exe}.bak"

REM update.bat 자체 삭제
del "%~f0"
"""
        
        # 배치 파일 작성
        with open(bat_path, 'w', encoding=BATCH_ENCODING) as f:
            f.write(bat_content)
        
        log.info(f"update.bat 생성 완료: {bat_path}")
        
        # 배치 파일 실행
        subprocess.Popen(
            [bat_path],
            creationflags=subprocess.CREATE_NO_WINDOW,
            shell=True
        )
        
        log.info("update.bat 실행 완료")
        return True
        
    except Exception as e:
        log.error(f"업데이트 적용 실패: {e}", exc_info=True)
        return False
