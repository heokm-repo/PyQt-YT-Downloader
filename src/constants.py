"""
상수 정의 모듈
설정 키값, 기본값, 상태값 등을 한곳에 모아 관리
"""
from enum import Enum
from locales import set_language

# 설정 키 (Settings Keys)
KEY_DOWNLOAD_FOLDER = 'download_folder'
KEY_VIDEO_QUALITY = 'video_quality'
KEY_AUDIO_QUALITY = 'audio_quality'
KEY_FORMAT = 'format'
KEY_MAX_DOWNLOADS = 'max_downloads'
KEY_NORMALIZE_AUDIO = 'normalize_audio'
KEY_USE_ACCELERATION = 'use_acceleration'
KEY_COOKIES_BROWSER = 'cookies_browser'
KEY_LANGUAGE = 'language'

# 기본값 (Defaults)
APP_VERSION = 'v1.2.0'  # 앱 버전
DEFAULT_VIDEO_QUALITY = 'best'
DEFAULT_AUDIO_QUALITY = 'best'
DEFAULT_FORMAT = 'mp4'
DEFAULT_MAX_DOWNLOADS = 3
DEFAULT_ACCELERATION = False
DEFAULT_NORMALIZE = False
DEFAULT_COOKIES_BROWSER = ''

# 설정 다이얼로그 옵션
VIDEO_QUALITY_OPTIONS = ['best', '1080p', '720p', '480p', '360p', 'worst']
AUDIO_QUALITY_OPTIONS = ['best', '320k', '256k', '192k', '128k', 'worst']
FORMAT_OPTIONS = ['mp4', 'mkv', 'webm', 'mp3', 'm4a', 'wav']
VIDEO_FORMATS = ['mp4', 'mkv', 'webm']
AUDIO_FORMATS = ['mp3', 'm4a', 'wav']
MAX_DOWNLOADS_RANGE = (1, 10)

# 쿠키 브라우저 매핑
COOKIES_BROWSER_DEFAULT = 'default'

# --- Core Logic Constants (Moved from function) ---
# Scheduler
SCHEDULER_PRIORITY_NORMAL = 0

# URL URLs and Domains
DOMAIN_YOUTU_BE = 'youtu.be'

# Workers / Download Status
STATUS_DOWNLOADING = 'downloading'
STATUS_FINISHED = 'finished'
STATUS_POSTPROCESSING = 'postprocessing'
STATUS_ERROR = 'error'
STATUS_STOPPED = 'stopped'

# Dialog Choices
DLG_CHOICE_PLAYLIST_IDX = 0
DLG_CHOICE_VIDEO_IDX = 1

# Extensions
EXT_PART = '.part'
EXT_YTDL = '.ytdl'

# YTDLP Options
YTDLP_TIMEOUT = 30
YTDLP_RETRIES = '10'
DEFAULT_ENCODING = 'utf-8'

# --- End Core Logic Constants ---

# 언어 변경 함수
def change_language(lang_code: str):
    """언어를 변경합니다."""
    set_language(lang_code)

# 메인 윈도우 제목
APP_TITLE = "YT Downloader"

# 스레드 대기 시간 (밀리초)
WORKER_TERMINATE_WAIT_MS = 1000  # 워커 종료 대기 시간 (1초)
WORKER_SHUTDOWN_WAIT_MS = 2000   # 워커 종료 대기 시간 (2초)
WORKER_CLEANUP_WAIT_MS = 5000    # 워커 정리 대기 시간 (5초)

# 워커 관련 상수
QUEUE_TIMEOUT_SEC = 1.0  # 큐 타임아웃 (초)
BYTES_PER_KB = 1024  # 킬로바이트
BYTES_PER_MB = 1024 * 1024  # 메가바이트

# 다운로드 관련 메시지 (Logic Only)
ERROR_INVALID_URL = "Invalid URL"
MSG_PAUSED_BY_USER = "PAUSED_BY_USER"
MSG_DOWNLOAD_COMPLETE = "완료" # Logic key used in youtube_handler.py

# 히스토리 및 작업 관리 관련
HISTORY_DB_FILENAME = 'history.db'
TASKS_JSON_FILENAME = 'tasks.json'
HISTORY_TABLE_NAME = 'downloads'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # SQLite 날짜 포맷

# 플레이리스트 관련
PLAYLIST_VIDEO_URL_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"

# 메타데이터 기본값
DEFAULT_PLAYLIST_TITLE = "PlayList"
DEFAULT_UPLOADER = "Unknown"
DEFAULT_VIDEO_TITLE = "No Title"

# 다운로드 설정 상수
CONCURRENT_FRAGMENT_DOWNLOADS = 6  # 멀티 스레드 다운로드 수
LOUDNORM_I = -14  # 오디오 정규화 강도
LOUDNORM_TP = -1  # 오디오 정규화 True Peak
OUTPUT_TEMPLATE = '%(title)s.%(ext)s'  # yt-dlp 출력 파일명 템플릿
AUDIO_CHANNELS = 2  # 오디오 채널 수 (스테레오)
LOUDNORM_FILTER = f'loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}'  # FFmpeg loudnorm 필터

# 포맷 관련 상수
FORMAT_MP4 = 'mp4'
FORMAT_MKV = 'mkv'
FORMAT_WEBM = 'webm'
FORMAT_MP3 = 'mp3'
FORMAT_M4A = 'm4a'
FORMAT_WAV = 'wav'
FORMAT_BESTAUDIO = 'bestaudio/best'
MEDIA_EXTENSIONS = ('.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.wav')  # 지원하는 미디어 파일 확장자

# YouTube URL 관련
YOUTUBE_PLAYLIST_URL_PREFIX = 'https://www.youtube.com/playlist?list='
YOUTUBE_SHORTS_PATH = '/shorts/'


# UI Symbols (Moved from strings.py)
MSG_0_PERCENT = "0%"
BTN_TEXT_CLOSE_X = "✕"
BTN_MINIMIZE = "─"

class TaskStatus(Enum):
    """작업 상태를 나타내는 Enum"""
    WAITING = 'waiting'
    DOWNLOADING = 'downloading'
    FINISHED = 'finished'
    FAILED = 'failed'
    PAUSED = 'paused'
    
    @classmethod
    def from_string(cls, value: str) -> 'TaskStatus':
        """문자열에서 TaskStatus로 변환 (하위 호환성)"""
        # 대소문자 무관하게 매칭 (기존 데이터 호환)
        value_lower = value.lower() if value else ''
        for status in cls:
            if status.value == value_lower:
                return status
        return cls.WAITING  # 기본값
    
    def __str__(self) -> str:
        return self.value

# Updater Constants
GITHUB_REPO_OWNER = "heokm-repo"
GITHUB_REPO_NAME = "PyQt-YT-Downloader"
UPDATE_TEMP_FILENAME = "YTDownloader_new.exe"
UPDATE_BATCH_FILENAME = "update.bat"
BATCH_ENCODING = 'cp949'

# Uninstaller Constants
UNINSTALL_BATCH_FILENAME = "uninstall.bat"
UNINSTALL_VBS_FILENAME = "uninstall_silent.vbs"
APPDATA_DIR_NAME = "YTDownloader"

# Bin Manager Constants
FFMPEG_ZIP_NAME_WIN = "ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_ZIP_NAME_LINUX = "ffmpeg-master-latest-linux64-gpl.tar.xz"
FFMPEG_EXE_INTERNAL_PATH = "bin/ffmpeg.exe"
FFMPEG_EXE_INTERNAL_PATH_ROOT = "ffmpeg.exe"

# Logger Constants
LOG_FILE_NAME = "app.log"
LOGGER_NAME = "YTDownloader"

# Utils Constants
YOUTUBE_URL_PATTERNS = [
    r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
    r'(?:https?://)?(?:www\.)?youtu\.be/([^&\n?#]+)', 
    r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^&\n?#]+)',
    r'(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=([^&\n?#]+)',
    r'(?:https?://)?(?:www\.)?youtube\.com/live/([^&\n?#]+)',
    r'(?:https?://)?(?:www\.)?youtube\.com/(?:embed|v)/([^&\n?#]+)'
]
PATH_MAC_APP_DATA = '~/Library/Application Support'
PATH_LINUX_APP_DATA = '~/.local/share'

# Main Constants
ORGANIZATION_NAME = "YTDownloader"
SRC_DIR_NAME = "src"
REQUIREMENTS_FILENAME = "requirements.txt"
