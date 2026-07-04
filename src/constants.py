"""Shared constants for settings keys, default values, status values, and external integrations."""
from enum import Enum
from locales import set_language

# Settings Keys
KEY_DOWNLOAD_FOLDER = 'download_folder'
KEY_VIDEO_QUALITY = 'video_quality'
KEY_AUDIO_QUALITY = 'audio_quality'
KEY_FORMAT = 'format'
KEY_MAX_DOWNLOADS = 'max_downloads'
KEY_NORMALIZE_AUDIO = 'normalize_audio'
KEY_USE_ACCELERATION = 'use_acceleration'
KEY_LANGUAGE = 'language'

# Defaults
APP_VERSION = 'v2.1.1'  # App version
DEFAULT_VIDEO_QUALITY = 'best'
DEFAULT_AUDIO_QUALITY = 'best'
DEFAULT_FORMAT = 'mp4'
DEFAULT_MAX_DOWNLOADS = 3
DEFAULT_ACCELERATION = False
DEFAULT_NORMALIZE = False

# Settings dialog options
VIDEO_QUALITY_OPTIONS = ['best', '1080p', '720p', '480p', '360p', 'worst']
AUDIO_QUALITY_OPTIONS = ['best', '320k', '256k', '192k', '128k', 'worst']
FORMAT_OPTIONS = ['mp4', 'mkv', 'webm', 'mp3', 'm4a', 'wav']
VIDEO_FORMATS = ['mp4', 'mkv', 'webm']
AUDIO_FORMATS = ['mp3', 'm4a', 'wav']
MAX_DOWNLOADS_RANGE = (1, 10)


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

# Language helper
def change_language(lang_code: str):
    """Change the active UI language."""
    set_language(lang_code)

# Main window title
APP_TITLE = "YT Downloader"

# Thread wait times in milliseconds
WORKER_TERMINATE_WAIT_MS = 1000  # Worker termination wait time (1 second)
WORKER_SHUTDOWN_WAIT_MS = 2000   # Worker shutdown wait time (2 seconds)
WORKER_CLEANUP_WAIT_MS = 5000    # Worker cleanup wait time (5 seconds)

# Worker constants
QUEUE_TIMEOUT_SEC = 1.0  # Queue timeout in seconds
BYTES_PER_KB = 1024  # Kilobytes
BYTES_PER_MB = 1024 * 1024  # Megabytes

# Download-related logic messages
ERROR_INVALID_URL = "Invalid URL"
MSG_PAUSED_BY_USER = "PAUSED_BY_USER"
MSG_DOWNLOAD_COMPLETE = "완료" # Logic key used in download_handler.py

# History and task-management constants
HISTORY_DB_FILENAME = 'history.db'
TASKS_JSON_FILENAME = 'tasks.json'
HISTORY_TABLE_NAME = 'downloads'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # SQLite date format

# Playlist constants
PLAYLIST_VIDEO_URL_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"

# Metadata defaults
DEFAULT_PLAYLIST_TITLE = "PlayList"
DEFAULT_UPLOADER = "Unknown"
DEFAULT_VIDEO_TITLE = "No Title"

# Temporary file directory
YTDL_TEMP_DIR = '.ytdl_temp'

# Download setting constants
CONCURRENT_FRAGMENT_DOWNLOADS = 6  # Number of concurrent fragment downloads
LOUDNORM_I = -14  # Audio normalization intensity
LOUDNORM_TP = -1  # Audio normalization true peak
OUTPUT_TEMPLATE = '%(title)s.%(ext)s'  # yt-dlp output filename template
AUDIO_CHANNELS = 2  # Number of audio channels (stereo)
LOUDNORM_FILTER = f'loudnorm=I={LOUDNORM_I}:TP={LOUDNORM_TP}'  # FFmpeg loudnorm filter

# Format constants
FORMAT_MP4 = 'mp4'
FORMAT_MKV = 'mkv'
FORMAT_WEBM = 'webm'
FORMAT_MP3 = 'mp3'
FORMAT_M4A = 'm4a'
FORMAT_WAV = 'wav'
FORMAT_BESTAUDIO = 'bestaudio/best'
MEDIA_EXTENSIONS = ('.mp4', '.mkv', '.webm', '.mp3', '.m4a', '.wav')  # Supported media file extensions

# YouTube URL constants
YOUTUBE_PLAYLIST_URL_PREFIX = 'https://www.youtube.com/playlist?list='
YOUTUBE_SHORTS_PATH = '/shorts/'


# UI Symbols (Moved from strings.py)
MSG_0_PERCENT = "0%"
BTN_TEXT_CLOSE_X = "✕"
BTN_MINIMIZE = "─"

class TaskStatus(Enum):
    """Enum for task states."""
    WAITING = 'waiting'
    DOWNLOADING = 'downloading'
    FINISHED = 'finished'
    FAILED = 'failed'
    PAUSED = 'paused'
    
    @classmethod
    def from_string(cls, value: str) -> 'TaskStatus':
        """Convert a string to TaskStatus for backward compatibility."""
        # Match case-insensitively for compatibility with existing data
        value_lower = value.lower() if value else ''
        for status in cls:
            if status.value == value_lower:
                return status
        return cls.WAITING  # Default value
    
    def __str__(self) -> str:
        return self.value

# Updater Constants
GITHUB_REPO_OWNER = "heokm-repo"
GITHUB_REPO_NAME = "PyQt-YT-Downloader"
GITHUB_API_BASE_URL = "https://api.github.com/repos"
APP_RELEASE_API_URL = f"{GITHUB_API_BASE_URL}/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
APP_UPDATE_ASSET_PREFIX = "setup"
APP_UPDATE_ASSET_EXTENSION = ".exe"
UPDATE_TEMP_FILENAME = "YTDownloader_Setup.exe"
APP_UPDATE_TEMP_ENV_VARS = ("TEMP", "TMP")
APP_UPDATE_TEMP_FALLBACK_DIR = "/tmp"
INNO_SETUP_RUN_AFTER_INSTALL_ARG = "/RUNAFTERINSTALL"
INNO_SETUP_INSTALL_ARGS = (
    "/SILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART",
    "/CLOSEAPPLICATIONS",
    INNO_SETUP_RUN_AFTER_INSTALL_ARG,
)

# Uninstaller Constants
APPDATA_DIR_NAME = "YTDownloader"
APPDATA_ENV_VAR = "APPDATA"
INNO_UNINSTALLER_FILENAME = "unins000.exe"
INNO_UNINSTALL_ARGS = ("/SILENT",)
WINDOWS_EXPLORER_COMMAND = "explorer"
WINDOWS_EXPLORER_SELECT_PREFIX = "/select,"

# Settings / Path Constants
SETTINGS_FILENAME = 'settings.json'
LEGACY_SAVE_PATH_KEY = 'save_path'
DOWNLOAD_FOLDER_NAME = APPDATA_DIR_NAME
FALLBACK_DOWNLOAD_FOLDER_NAME = APPDATA_DIR_NAME
USER_DOWNLOADS_DIR_NAME = 'Downloads'
WINDOWS_PROTECTED_FOLDER_ENV_VARS = ('ProgramFiles', 'ProgramFiles(x86)', 'ProgramW6432', 'SystemRoot', 'windir')
WINDOWS_SYSTEM_DRIVE_ENV_VAR = 'SystemDrive'
WINDOWS_SYSTEM_DRIVE_FALLBACK = 'C:'
WINDOWS_PROTECTED_DEFAULT_FOLDERS = ('Program Files', 'Program Files (x86)', 'Windows')
DOWNLOAD_FOLDER_WRITE_TEST_PREFIX = '.write_test_'
ERR_DOWNLOAD_FOLDER_PROTECTED = 'Protected Windows system folder cannot be used as a download folder.'
ERR_DOWNLOAD_FOLDER_EMPTY = 'Download folder path is empty.'
ERR_DOWNLOAD_FOLDER_NOT_DIRECTORY = 'Path is not a directory.'

# Bin Manager Constants
YTDLP_BINARY = 'yt-dlp.exe'
FFMPEG_BINARY = 'ffmpeg.exe'
QUICKJS_BINARY = 'qjs.exe'
YTDLP_RELEASE_API_URL = f"{GITHUB_API_BASE_URL}/yt-dlp/yt-dlp/releases/latest"
FFMPEG_RELEASE_API_URL = f"{GITHUB_API_BASE_URL}/BtbN/FFmpeg-Builds/releases/latest"
QUICKJS_RELEASE_API_URL = f"{GITHUB_API_BASE_URL}/quickjs-ng/quickjs/releases/latest"
FFMPEG_ZIP_NAME_WIN = "ffmpeg-master-latest-win64-gpl.zip"
FFMPEG_EXE_INTERNAL_PATH = "bin/ffmpeg.exe"
FFMPEG_EXE_INTERNAL_PATH_ROOT = "ffmpeg.exe"
QUICKJS_ASSET_NAME = 'qjs-windows-x86_64.exe'
BIN_VERSION_FILENAME = '.version.json'
BIN_UPDATE_CHECK_INTERVAL_HOURS = 12

# Network / Process Constants
HTTP_API_TIMEOUT_SEC = 10
HTTP_DOWNLOAD_TIMEOUT_SEC = 30
HTTP_DOWNLOAD_CHUNK_SIZE = 8192
PROCESS_TERMINATE_WAIT_SEC = 5
PROCESS_MONITOR_INTERVAL_SEC = 0.1
STARTUP_STATUS_SETTLE_DELAY_SEC = 0.1
THREAD_JOIN_SHORT_TIMEOUT_SEC = 1
YTDLP_DOWNLOAD_PROCESS_TIMEOUT_SEC = 60
DOWNLOAD_DIALOG_AUTO_CLOSE_MS = 1000
COOKIE_FALLBACK_EXPIRY_DAYS = 365
SECONDS_PER_DAY = 24 * 60 * 60
COOKIE_FALLBACK_EXPIRY_SEC = COOKIE_FALLBACK_EXPIRY_DAYS * SECONDS_PER_DAY
HTTP_USER_AGENT_HEADER = b"User-Agent"
THUMBNAIL_USER_AGENT = b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# YouTube Login Constants
YOUTUBE_LOGIN_URL = "https://accounts.google.com/ServiceLogin?service=youtube&uilel=3&passive=true&continue=https%3A%2F%2Fwww.youtube.com%2Fsignin"
YOUTUBE_ROBOTS_URL = "https://www.youtube.com/robots.txt"
YOUTUBE_DOMAIN_FRAGMENT = "youtube.com"
GOOGLE_ACCOUNTS_DOMAIN = "accounts.google.com"
YOUTUBE_ROBOTS_PATH_FRAGMENT = "robots.txt"
WEBENGINE_STORAGE_DIR = "webengine_storage"
WEBENGINE_CACHE_DIR = "webengine_cache"

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

# Main Constants
ORGANIZATION_NAME = "YTDownloader"
SRC_DIR_NAME = "src"
REQUIREMENTS_FILENAME = "requirements.txt"

# Startup Dependency Constants
STARTUP_REQUIRED_DEPENDENCY_SPECS = (
    ("PyQt5.QtWidgets", "PyQt5"),
    ("requests", "requests"),
    ("packaging", "packaging"),
    ("qtawesome", "qtawesome"),
    ("yt_dlp", "yt-dlp"),
)
STARTUP_OPTIONAL_DEPENDENCY_SPECS = (
    ("PyQt5.QtWebEngineWidgets", "PyQtWebEngine", "in-app login"),
)
