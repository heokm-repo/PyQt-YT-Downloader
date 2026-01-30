import sys
import os
import re
from typing import Optional

APP_NAME = "YTDownloader"


def get_base_path() -> str:
    """실행 파일의 기본 경로를 반환 (PyInstaller 호환)"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_path() -> str:
    """
    OS별 표준 사용자 데이터 경로 반환
    Windows: %APPDATA%\YTDownloader
    macOS: ~/Library/Application Support/YTDownloader
    Linux: ~/.local/share/YTDownloader
    """
    if sys.platform == 'win32':
        base_path = os.getenv('APPDATA')
    elif sys.platform == 'darwin':
        base_path = os.path.expanduser('~/Library/Application Support')
    else:
        base_path = os.path.expanduser('~/.local/share')

    if not base_path:
        return get_base_path()
    
    data_path = os.path.join(base_path, APP_NAME)
    
    if not os.path.exists(data_path):
        try:
            os.makedirs(data_path, exist_ok=True)
        except OSError:
            return get_base_path()
            
    return data_path

def get_ffmpeg_path() -> Optional[str]:
    """
    FFmpeg 실행 파일 경로 반환
    - bin_manager에서 관리하는 외부 바이너리 사용
    """
    from utils.bin_manager import get_ffmpeg_path as get_bin_ffmpeg
    return get_bin_ffmpeg()

def validate_url(url: str) -> bool:
    """
    YouTube URL 유효성 검사
    지원 형식: 일반 영상, 단축 URL, 숏츠, 플레이리스트, 라이브, 임베드
    """
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)', 
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/live/([^&\n?#]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/(?:embed|v)/([^&\n?#]+)'
    ]
    
    return any(re.search(pattern, url) for pattern in youtube_patterns)

def format_bytes(b) -> str:
    """바이트를 사람이 읽기 쉬운 형태로 변환"""
    if b is None:
        return "0 B"
    
    try:
        b = float(b)
    except (ValueError, TypeError):
        return "? B"
        
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    i = 0
    while b >= 1024 and i < len(units) - 1:
        b /= 1024.0
        i += 1
    return f"{b:.2f} {units[i]}"