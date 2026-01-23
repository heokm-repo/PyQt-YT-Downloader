"""
상수 정의 모듈
설정 키값, 기본값, 상태값 등을 한곳에 모아 관리
"""
from enum import Enum
from locales import get_string, set_language, get_language, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE

# 설정 키 (Settings Keys)
KEY_DOWNLOAD_FOLDER = 'download_folder'
KEY_VIDEO_QUALITY = 'video_quality'
KEY_AUDIO_QUALITY = 'audio_quality'
KEY_FORMAT = 'format'
KEY_MAX_DOWNLOADS = 'max_downloads'
KEY_NORMALIZE_AUDIO = 'normalize_audio'
KEY_USE_ACCELERATION = 'use_acceleration'
KEY_COOKIES_BROWSER = 'cookies_browser'
KEY_LANGUAGE = 'language'  # 언어 설정 키 추가

# 기본값 (Defaults)
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
FORMAT_OPTIONS = ['mp4', 'mkv', 'webm', 'mp3']
MAX_DOWNLOADS_RANGE = (1, 10)

# 쿠키 브라우저 매핑
COOKIES_BROWSER_VALUES = ['', 'chrome', 'edge', 'firefox', 'whale']
COOKIES_BROWSER_DEFAULT = 'default'  # 기본 브라우저 값

def get_cookies_browser_display():
    """언어별 쿠키 브라우저 표시 목록을 반환합니다."""
    return [
        get_string('COOKIES_BROWSER_DISPLAY_0'),
        get_string('COOKIES_BROWSER_DISPLAY_1'),
        get_string('COOKIES_BROWSER_DISPLAY_2'),
        get_string('COOKIES_BROWSER_DISPLAY_3'),
        get_string('COOKIES_BROWSER_DISPLAY_4'),
    ]

# 하위 호환성을 위한 변수 (동적 함수로 대체)
COOKIES_BROWSER_DISPLAY = get_cookies_browser_display()

# 설정 다이얼로그 크기
SETTINGS_DIALOG_WIDTH = 450
SETTINGS_DIALOG_HEIGHT = 580

# 설정 다이얼로그 UI 크기 상수
SETTINGS_INPUT_HEIGHT = 35
SETTINGS_BUTTON_HEIGHT = 40
SETTINGS_BUTTON_WIDTH = 80
SETTINGS_TITLE_BAR_HEIGHT = 30
SETTINGS_CLOSE_BUTTON_SIZE = 24
SETTINGS_SHADOW_BLUR_RADIUS = 15
SETTINGS_CONTAINER_MARGIN = 10
SETTINGS_CONTENT_MARGIN = (25, 20, 25, 25)
SETTINGS_CONTENT_SPACING = 20
SETTINGS_SHADOW_ALPHA = 30  # 그림자 투명도

# 설정 다이얼로그 UI 텍스트 (언어별 문자열은 locales 모듈에서 가져옴)
# 언어 변경 시 업데이트되는 동적 상수들
def _update_string_constants():
    """언어별 문자열 상수를 업데이트합니다."""
    global SETTINGS_DIALOG_TITLE, SETTINGS_SECTION_SAVE_LOCATION, SETTINGS_BROWSE_BUTTON_TEXT
    global SETTINGS_SECTION_QUALITY_FORMAT, SETTINGS_LABEL_VIDEO_QUALITY, SETTINGS_LABEL_AUDIO_QUALITY
    global SETTINGS_LABEL_FORMAT, SETTINGS_SECTION_GENERAL, SETTINGS_LABEL_MAX_DOWNLOADS
    global SETTINGS_SECTION_ADVANCED, SETTINGS_CHECKBOX_NORMALIZE, SETTINGS_CHECKBOX_ACCELERATION
    global SETTINGS_LABEL_COOKIES, SETTINGS_BUTTON_CANCEL, SETTINGS_BUTTON_SAVE
    global SETTINGS_FOLDER_DIALOG_TITLE, SETTINGS_ERROR_TITLE, SETTINGS_ERROR_NO_FOLDER
    global SETTINGS_ERROR_CANNOT_CREATE_FOLDER, SETTINGS_ERROR_INVALID_FOLDER
    global COOKIES_BROWSER_DISPLAY, URL_INPUT_PLACEHOLDER, DOWNLOAD_BUTTON_TEXT
    global EMPTY_STATE_MESSAGE, STATUS_BAR_DEFAULT_TEXT, STATUS_TEXT_WAITING
    global STATUS_TEXT_DOWNLOADING, STATUS_TEXT_PAUSED, STATUS_TEXT_IN_PROGRESS
    global STATUS_TEXT_WAITING_DOTS, STATUS_TEXT_PAUSED_SAVED, STATUS_TEXT_PREVIOUS_FAILED
    global MSG_READY, MSG_SMART_PASTE_STARTED, MSG_DOWNLOAD_ENABLED, MSG_DOWNLOAD_PAUSED
    global MSG_DOWNLOAD_CANCELLED, MSG_ADDED_TO_QUEUE, MSG_PLAYLIST_ANALYZING
    global MSG_PLAYLIST_REGISTERING, MSG_PLAYLIST_ADDED, MSG_ERROR_COUNT, MSG_COMPLETED_COUNT
    global MSG_NO_NEW_VIDEOS, MSG_PLAYLIST_FETCH_ERROR, MSG_DOWNLOAD_COMPLETE
    global MSG_NOT_PLAYLIST_URL, MSG_CANNOT_FETCH_INFO, DUPLICATE_CHECK_TITLE
    global DUPLICATE_MSG_ALREADY_DOWNLOADED, DUPLICATE_MSG_IN_QUEUE, DUPLICATE_MSG_ASK_OVERWRITE
    global DIALOG_DUPLICATE_VIDEOS_TITLE, DIALOG_DUPLICATE_VIDEOS_MESSAGE
    global DIALOG_RESUME_DOWNLOAD_TITLE, DIALOG_RESUME_DOWNLOAD_MESSAGE, DIALOG_NO_NEW_VIDEOS_TITLE
    global PLAYLIST_VIDEO_TITLE_TEMPLATE, WARNING_PLAYLIST_WORKER_TIMEOUT
    global TITLE_BAR_MINIMIZE_BUTTON_TEXT, TITLE_BAR_CLOSE_BUTTON_TEXT
    
    # 설정 다이얼로그
    SETTINGS_DIALOG_TITLE = get_string('SETTINGS_DIALOG_TITLE', "설정")
    SETTINGS_SECTION_SAVE_LOCATION = get_string('SETTINGS_SECTION_SAVE_LOCATION', "저장 위치")
    SETTINGS_BROWSE_BUTTON_TEXT = get_string('SETTINGS_BROWSE_BUTTON_TEXT', "찾아보기")
    SETTINGS_SECTION_QUALITY_FORMAT = get_string('SETTINGS_SECTION_QUALITY_FORMAT', "품질 및 포맷")
    SETTINGS_LABEL_VIDEO_QUALITY = get_string('SETTINGS_LABEL_VIDEO_QUALITY', "화질:")
    SETTINGS_LABEL_AUDIO_QUALITY = get_string('SETTINGS_LABEL_AUDIO_QUALITY', "음질:")
    SETTINGS_LABEL_FORMAT = get_string('SETTINGS_LABEL_FORMAT', "포맷:")
    SETTINGS_SECTION_GENERAL = get_string('SETTINGS_SECTION_GENERAL', "일반 설정")
    SETTINGS_LABEL_MAX_DOWNLOADS = get_string('SETTINGS_LABEL_MAX_DOWNLOADS', "최대 다운로드 수:")
    SETTINGS_SECTION_ADVANCED = get_string('SETTINGS_SECTION_ADVANCED', "고급 기능")
    SETTINGS_CHECKBOX_NORMALIZE = get_string('SETTINGS_CHECKBOX_NORMALIZE', "음량 평준화 (Loudness Normalization)")
    SETTINGS_CHECKBOX_ACCELERATION = get_string('SETTINGS_CHECKBOX_ACCELERATION', "다운로드 가속 (멀티 스레드)")
    SETTINGS_LABEL_COOKIES = get_string('SETTINGS_LABEL_COOKIES', "쿠키 연동:")
    SETTINGS_BUTTON_CANCEL = get_string('SETTINGS_BUTTON_CANCEL', "취소")
    SETTINGS_BUTTON_SAVE = get_string('SETTINGS_BUTTON_SAVE', "저장")
    SETTINGS_FOLDER_DIALOG_TITLE = get_string('SETTINGS_FOLDER_DIALOG_TITLE', "다운로드 폴더 선택")
    SETTINGS_ERROR_TITLE = get_string('SETTINGS_ERROR_TITLE', "오류")
    SETTINGS_ERROR_NO_FOLDER = get_string('SETTINGS_ERROR_NO_FOLDER', "다운로드 폴더를 선택해주세요.")
    SETTINGS_ERROR_CANNOT_CREATE_FOLDER = get_string('SETTINGS_ERROR_CANNOT_CREATE_FOLDER', "폴더를 생성할 수 없습니다:\n{error}")
    SETTINGS_ERROR_INVALID_FOLDER = get_string('SETTINGS_ERROR_INVALID_FOLDER', "선택한 경로가 유효한 폴더가 아닙니다.")
    COOKIES_BROWSER_DISPLAY = get_cookies_browser_display()
    
    # 메인 윈도우
    URL_INPUT_PLACEHOLDER = get_string('URL_INPUT_PLACEHOLDER', "YouTube 링크 입력")
    DOWNLOAD_BUTTON_TEXT = get_string('DOWNLOAD_BUTTON_TEXT', "다운로드")
    EMPTY_STATE_MESSAGE = get_string('EMPTY_STATE_MESSAGE', "다운로드할 영상이 없습니다.\n상단에 URL을 입력하여 시작하세요.")
    STATUS_BAR_DEFAULT_TEXT = get_string('STATUS_BAR_DEFAULT_TEXT', "준비됨")
    TITLE_BAR_MINIMIZE_BUTTON_TEXT = get_string('TITLE_BAR_MINIMIZE_BUTTON_TEXT', "─")
    TITLE_BAR_CLOSE_BUTTON_TEXT = get_string('TITLE_BAR_CLOSE_BUTTON_TEXT', "✕")
    
    # 작업 상태
    STATUS_TEXT_WAITING = get_string('STATUS_TEXT_WAITING', '대기 중')
    STATUS_TEXT_DOWNLOADING = get_string('STATUS_TEXT_DOWNLOADING', '다운로드 중')
    STATUS_TEXT_PAUSED = get_string('STATUS_TEXT_PAUSED', '일시정지됨')
    STATUS_TEXT_IN_PROGRESS = get_string('STATUS_TEXT_IN_PROGRESS', '진행 중')
    STATUS_TEXT_WAITING_DOTS = get_string('STATUS_TEXT_WAITING_DOTS', '대기 중...')
    STATUS_TEXT_PAUSED_SAVED = get_string('STATUS_TEXT_PAUSED_SAVED', '일시정지됨 (저장됨)')
    STATUS_TEXT_PREVIOUS_FAILED = get_string('STATUS_TEXT_PREVIOUS_FAILED', '이전 작업 실패')
    
    # 메시지
    MSG_READY = get_string('MSG_READY', "준비됨")
    MSG_SMART_PASTE_STARTED = get_string('MSG_SMART_PASTE_STARTED', "스마트 붙여넣기: 다운로드 시작됨")
    MSG_DOWNLOAD_ENABLED = get_string('MSG_DOWNLOAD_ENABLED', "다운로드 활성화됨")
    MSG_DOWNLOAD_PAUSED = get_string('MSG_DOWNLOAD_PAUSED', "다운로드 일시정지됨")
    MSG_DOWNLOAD_CANCELLED = get_string('MSG_DOWNLOAD_CANCELLED', "다운로드가 취소되었습니다.")
    MSG_ADDED_TO_QUEUE = get_string('MSG_ADDED_TO_QUEUE', "대기열에 추가되었습니다.")
    MSG_PLAYLIST_ANALYZING = get_string('MSG_PLAYLIST_ANALYZING', "플레이리스트를 분석하는 중...")
    MSG_PLAYLIST_REGISTERING = get_string('MSG_PLAYLIST_REGISTERING', "플레이리스트 {count}개 영상 등록 중...")
    MSG_PLAYLIST_ADDED = get_string('MSG_PLAYLIST_ADDED', "플레이리스트 {count}개 영상이 대기열에 추가되었습니다.")
    MSG_ERROR_COUNT = get_string('MSG_ERROR_COUNT', "오류: {count}개")
    MSG_COMPLETED_COUNT = get_string('MSG_COMPLETED_COUNT', "완료: {finished} / {total}")
    MSG_NO_NEW_VIDEOS = get_string('MSG_NO_NEW_VIDEOS', "추가할 새 영상이 없습니다.")
    MSG_PLAYLIST_FETCH_ERROR = get_string('MSG_PLAYLIST_FETCH_ERROR', "플레이리스트에서 영상을 가져올 수 없습니다.")
    MSG_DOWNLOAD_COMPLETE = get_string('MSG_DOWNLOAD_COMPLETE', "완료")
    MSG_NOT_PLAYLIST_URL = get_string('MSG_NOT_PLAYLIST_URL', "플레이리스트 URL이 아닙니다.")
    MSG_CANNOT_FETCH_INFO = get_string('MSG_CANNOT_FETCH_INFO', "정보를 가져올 수 없습니다.")
    
    # 다이얼로그
    DIALOG_DUPLICATE_VIDEOS_TITLE = get_string('DIALOG_DUPLICATE_VIDEOS_TITLE', "중복 영상 확인")
    DIALOG_DUPLICATE_VIDEOS_MESSAGE = get_string('DIALOG_DUPLICATE_VIDEOS_MESSAGE', "플레이리스트 {total}개 중 {duplicate}개는 이미 다운로드한 영상입니다.\n중복된 영상을 제외할까요?")
    DIALOG_RESUME_DOWNLOAD_TITLE = get_string('DIALOG_RESUME_DOWNLOAD_TITLE', "다운로드 재개")
    DIALOG_RESUME_DOWNLOAD_MESSAGE = get_string('DIALOG_RESUME_DOWNLOAD_MESSAGE', "이전에 다운로드중인 작업을 재개하시겠습니까?")
    DIALOG_NO_NEW_VIDEOS_TITLE = get_string('DIALOG_NO_NEW_VIDEOS_TITLE', "알림")
    
    # 중복 다운로드
    DUPLICATE_CHECK_TITLE = get_string('DUPLICATE_CHECK_TITLE', "중복 다운로드 확인")
    DUPLICATE_MSG_ALREADY_DOWNLOADED = get_string('DUPLICATE_MSG_ALREADY_DOWNLOADED', "이미 '{format}' 포맷으로 다운로드된 영상입니다.\n")
    DUPLICATE_MSG_IN_QUEUE = get_string('DUPLICATE_MSG_IN_QUEUE', "(현재 {status} 상태인 작업이 있습니다)\n")
    DUPLICATE_MSG_ASK_OVERWRITE = get_string('DUPLICATE_MSG_ASK_OVERWRITE', "\n다시 다운로드(덮어쓰기) 하시겠습니까?")
    
    # 플레이리스트
    PLAYLIST_VIDEO_TITLE_TEMPLATE = get_string('PLAYLIST_VIDEO_TITLE_TEMPLATE', "영상 ID: {video_id}")
    
    # 경고
    WARNING_PLAYLIST_WORKER_TIMEOUT = get_string('WARNING_PLAYLIST_WORKER_TIMEOUT', "플레이리스트 워커가 시간 내에 종료되지 않았습니다.")

# 언어 변경 함수
def change_language(lang_code: str):
    """언어를 변경하고 모든 문자열 상수를 업데이트합니다."""
    set_language(lang_code)
    _update_string_constants()

# 초기화: 기본 언어로 상수 업데이트
_update_string_constants()

SETTINGS_CLOSE_BUTTON_TEXT = "✕"  # 특수 문자는 언어와 무관

# 설정 다이얼로그 폰트
SETTINGS_FONT_FAMILY = "Segoe UI"
SETTINGS_TITLE_FONT_SIZE = 12
SETTINGS_SECTION_FONT_SIZE = 10

# 메인 윈도우 크기 및 위치
MAIN_WINDOW_X = 100
MAIN_WINDOW_Y = 100
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

# 메인 윈도우 제목 및 앱 정보
APP_TITLE = "YT Downloader"  # 앱 이름은 언어와 무관
APP_TITLE_COLOR = "#5F428B"

# 메인 윈도우 레이아웃
MAIN_LAYOUT_MARGINS = (3, 3, 3, 3)
MAIN_LAYOUT_SPACING = 5

# 타이틀 바
TITLE_BAR_HEIGHT = 30
TITLE_BAR_MARGINS = (10, 0, 10, 0)
TITLE_BAR_SPACING = 10
TITLE_BAR_FONT_FAMILY = "Segoe UI"
TITLE_BAR_FONT_SIZE = 11
TITLE_BAR_BUTTON_SIZE = 28  # 최소화/닫기 버튼
# TITLE_BAR_MINIMIZE_BUTTON_TEXT, TITLE_BAR_CLOSE_BUTTON_TEXT는 _update_string_constants()에서 설정됨

# URL 입력 섹션
URL_INPUT_SECTION_HEIGHT = 70
URL_INPUT_CONTAINER_MARGINS = (10, 8, 10, 8)
URL_INPUT_CONTAINER_SPACING = 10
# URL_INPUT_PLACEHOLDER는 _update_string_constants()에서 설정됨
URL_INPUT_HEIGHT = 40
URL_INPUT_FONT_FAMILY = "Segoe UI"
URL_INPUT_FONT_SIZE = 11

# 다운로드 버튼
# DOWNLOAD_BUTTON_TEXT는 _update_string_constants()에서 설정됨
DOWNLOAD_BUTTON_HEIGHT = 40
DOWNLOAD_BUTTON_WIDTH = 90
DOWNLOAD_BUTTON_FONT_FAMILY = "Segoe UI"
DOWNLOAD_BUTTON_FONT_SIZE = 10

# 설정 버튼
SETTINGS_BUTTON_TEXT = "⚙"
SETTINGS_BUTTON_FONT_FAMILY = "Segoe UI"
SETTINGS_BUTTON_FONT_SIZE = 12

# 작업 목록 섹션
TASK_LIST_MARGINS = (10, 0, 10, 0)
TASK_LIST_SPACING = 10
# EMPTY_STATE_MESSAGE는 _update_string_constants()에서 설정됨
EMPTY_STATE_FONT_FAMILY = "Segoe UI"
EMPTY_STATE_FONT_SIZE = 11

# 상태 표시줄
STATUS_BAR_HEIGHT = 30
STATUS_BAR_MARGINS = (10, 0, 10, 0)
STATUS_BAR_SPACING = 10
# STATUS_BAR_DEFAULT_TEXT는 _update_string_constants()에서 설정됨
STATUS_BAR_FONT_FAMILY = "Segoe UI"
STATUS_BAR_FONT_SIZE = 9
PROGRESS_SLIDER_MIN = 0
PROGRESS_SLIDER_MAX = 100
PROGRESS_SLIDER_DEFAULT = 0

# 작업 카드 UI 크기 상수
CARD_HEIGHT = 130
THUMBNAIL_WIDTH = 160
THUMBNAIL_HEIGHT = 90
BUTTON_SIZE = 40
BUTTON_FONT_SIZE = 15

# URL 입력 섹션 버튼 크기
TOGGLE_BUTTON_SIZE = 50  # 토글 버튼
SETTINGS_BUTTON_SIZE = 40  # 설정 버튼

# 버튼 색상 상수
COLOR_BTN_RED = "#F44336"
COLOR_BTN_GREEN = "#4CAF50"
COLOR_BTN_BLUE = "#2196F3"
COLOR_BTN_ORANGE = "#FF9800"
COLOR_BTN_GRAY = "#999999"

# 스레드 대기 시간 (밀리초)
WORKER_TERMINATE_WAIT_MS = 1000  # 워커 종료 대기 시간 (1초)
WORKER_SHUTDOWN_WAIT_MS = 2000   # 워커 종료 대기 시간 (2초)
WORKER_CLEANUP_WAIT_MS = 5000    # 워커 정리 대기 시간 (5초)

# 워커 관련 상수
QUEUE_TIMEOUT_SEC = 1.0  # 큐 타임아웃 (초)
BYTES_PER_KB = 1024  # 킬로바이트
BYTES_PER_MB = 1024 * 1024  # 메가바이트

# 다운로드 관련 메시지
ERROR_INVALID_URL = "Invalid URL"  # 기술적 메시지는 언어와 무관
MSG_PAUSED_BY_USER = "PAUSED_BY_USER"  # 내부 상태값은 언어와 무관
# MSG_DOWNLOAD_COMPLETE, MSG_NOT_PLAYLIST_URL, MSG_CANNOT_FETCH_INFO는 _update_string_constants()에서 설정됨

# 히스토리 및 작업 관리 관련
HISTORY_DB_FILENAME = 'history.db'
TASKS_JSON_FILENAME = 'tasks.json'
HISTORY_TABLE_NAME = 'downloads'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'  # SQLite 날짜 포맷

# 중복 다운로드 확인 메시지, 작업 상태 표시 텍스트, 메인 윈도우 상태 메시지, 
# 플레이리스트 관련, 다이얼로그 메시지, 워커 경고 메시지는 _update_string_constants()에서 설정됨

# 플레이리스트 관련 (URL 템플릿은 언어와 무관)
PLAYLIST_VIDEO_URL_TEMPLATE = "https://www.youtube.com/watch?v={video_id}"
# PLAYLIST_VIDEO_TITLE_TEMPLATE는 _update_string_constants()에서 설정됨

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
FORMAT_MP3 = 'mp3'
FORMAT_BESTAUDIO = 'bestaudio/best'
MEDIA_EXTENSIONS = ('.mp4', '.mkv', '.webm', '.mp3', '.m4a')  # 지원하는 미디어 파일 확장자

# YouTube URL 관련
YOUTUBE_PLAYLIST_URL_PREFIX = 'https://www.youtube.com/playlist?list='
YOUTUBE_SHORTS_PATH = '/shorts/'


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
