"""Korean string definitions."""
STRINGS = {
    # =========================================================================
    # 1. Common / Global
    # =========================================================================
    'BTN_OK': "확인",
    'BTN_YES': "예",
    'BTN_NO': "아니오",
    'BTN_CLOSE': "닫기",
    'BTN_CANCEL': "취소",
    'BTN_SAVE': "저장",
    'BTN_RESTART_NOW': "지금 다시 시작",
    'BTN_LATER': "나중에",

    'TITLE_WARNING': "경고",
    'TITLE_ERROR': "오류",

    # =========================================================================
    # 2. Main Window
    # =========================================================================
    'MAIN_URL_PLACEHOLDER': "영상 URL 입력",
    'BTN_DOWNLOAD': "다운로드",
    'MAIN_EMPTY_STATE': "다운로드할 영상이 없습니다.\n상단에 URL을 입력하여 시작하세요.",
    'MAIN_STATUS_READY': "준비됨",

    # =========================================================================
    # 3. Settings Dialog
    # =========================================================================
    'TITLE_SETTINGS': "설정",

    # Section: Save Location
    'TITLE_FOLDER_SELECT': "폴더 선택",
    'TITLE_LICENSE': "라이선스 정보",
    'SETTINGS_SEC_LOCATION': "저장 위치",
    'SETTINGS_BTN_BROWSE': "찾아보기",

    # Section: Quality & Format
    'SETTINGS_SEC_QUALITY': "품질 및 포맷",
    'SETTINGS_LABEL_VIDEO': "화질:",
    'SETTINGS_LABEL_AUDIO': "음질:",
    'SETTINGS_LABEL_FORMAT': "포맷:",
    'SETTINGS_HEADER_VIDEO': "=== 비디오 ===",
    'SETTINGS_HEADER_AUDIO': "=== 오디오 ===",

    # Section: General Settings
    'SETTINGS_SEC_GENERAL': "일반 설정",
    'SETTINGS_LABEL_MAX_DL': "최대 동시 다운로드 수:",
    'SETTINGS_LABEL_LANGUAGE': "언어 (Language):",
    'SETTINGS_LABEL_THEME': "테마:",
    'SETTINGS_THEME_LIGHT': "라이트",
    'SETTINGS_THEME_DARK': "다크",

    # Section: Advanced Features
    'SETTINGS_SEC_ADVANCED': "고급 기능",
    'SETTINGS_CHK_NORMALIZE': "음량 정규화",
    'SETTINGS_CHK_ACCEL': "다운로드 가속 (멀티 스레드)",
    'SETTINGS_CHK_COMPATIBILITY': "높은 호환성 모드",
    'SETTINGS_LABEL_COOKIES': "인앱 로그인:",
    'BTN_LOGIN': "로그인하기",
    'BTN_SAVE_CLOSE': "저장 및 닫기",
    'TITLE_LOGIN_BROWSER': "YouTube 로그인",
    'MSG_LOGIN_WAITING': "Google 계정으로 로그인해 주세요.",
    'MSG_LOGIN_SUCCESS': "로그인을 감지했습니다! ‘저장 및 닫기’를 클릭하세요.",
    'MSG_LOGIN_STABILIZING': "로그인 마무리 중...",
    'ERR_LOGIN_NO_COOKIES': "YouTube 쿠키를 가져오지 못했습니다!",
    'ERR_LOGIN_SAVE_FAILED': "저장 실패: {error}",

    'BTN_LOGOUT': "로그아웃",
    'TITLE_LOGOUT': "로그아웃",
    'MSG_LOGOUT_CONFIRM': "저장된 YouTube 쿠키와 브라우저 로그인 데이터를 삭제할까요?",
    'MSG_LOGOUT_SUCCESS': "저장된 쿠키와 브라우저 로그인 데이터를 삭제했습니다.",
    'ERR_LOGOUT_FAILED': "일부 로그인 데이터를 삭제하지 못했습니다. 로그인 창을 닫고 다시 시도해 주세요.",

    # Section: App Management
    'SETTINGS_SEC_APP_MANAGE': "앱 관리",
    'SETTINGS_LABEL_VERSION': "현재 버전:",
    'SETTINGS_BTN_CHECK_UPDATE': "업데이트 확인",
    'SETTINGS_BTN_UNINSTALL': "앱 제거",
    'SETTINGS_BTN_LICENSE': "라이선스 정보",
    'SETTINGS_BTN_SPONSOR': "후원하기",

    # Settings Errors
    'ERR_SETTINGS_NO_FOLDER': "다운로드 폴더를 선택해 주세요.",
    'ERR_SPONSOR_OPEN': "후원 페이지를 열 수 없습니다.",
    'MSG_DOWNLOAD_FOLDER_FALLBACK': "다운로드 폴더를 사용할 수 없어 저장 위치가 변경되었습니다.\n\n이전 저장 위치:\n{old_path}\n\n새 저장 위치:\n{new_path}\n\n사유:\n{reason}",

    # =========================================================================
    # 4. Status Messages
    # =========================================================================

    'STATUS_WAITING_DOTS': "대기 중...",

    'STATUS_DOWNLOADING_DOTS': "다운로드 중...",
    'STATUS_DOWNLOADING_SPEED': "다운로드 중 ({speed})",
    
    'STATUS_PAUSED': "일시 정지됨",
    'STATUS_PAUSED_SAVED': "일시 정지됨 (저장됨)",
    'STATUS_PAUSED_CANCELLED': "취소됨 (임시 파일 삭제됨)",
    'STATUS_IN_PROGRESS': "진행 중",

    
    'STATUS_CONVERTING': "변환 중...",

    'STATUS_COMPLETED': "완료",
    'STATUS_FAILED_FMT': "실패: {message}",
    'STATUS_PREPARING': "다운로드 준비 중...",
    'STATUS_NO_IMAGE': "이미지 없음",

    # =========================================================================
    # 5. Dialogs & Popups
    # =========================================================================
    
    # URL Choice
    'TITLE_CHOICE': "다운로드 방식 선택",
    'MSG_CHOICE_PLAYLIST': "이 URL은 영상과 플레이리스트 정보를 모두 포함하고 있습니다.\n\n무엇을 다운로드하시겠습니까?",
    'BTN_CHOICE_ALL': "플레이리스트 전체",
    'BTN_CHOICE_VIDEO': "이 영상만",

    # Duplicate / Resume
    'TITLE_DUPLICATE': "중복 영상 확인",
    'MSG_DUPLICATE_FOUND': "이미 다운로드함: {duplicate} / {total}\n중복 영상을 제외할까요?",
    'MSG_DUPLICATE_CHECK': "중복 다운로드 확인",
    'MSG_DUP_ALREADY_DONE': "이미 ‘{format}’ 형식으로 다운로드된 영상입니다.\n",
    'MSG_DUP_IN_QUEUE': "(이 작업은 현재 {status} 상태입니다)\n",
    'MSG_DUP_ASK_OVERWRITE': "\n다시 다운로드하여 덮어쓰시겠습니까?",
    'ERR_DUPLICATE_REPLACEMENT_TIMEOUT': "기존 다운로드가 제한 시간 안에 중지되지 않아 새 다운로드를 시작하지 않았습니다.",
    
    'TITLE_RESUME': "다운로드 재개",
    'MSG_RESUME_CONFIRM': "이전에 일시 정지된 다운로드를 재개하시겠습니까?",
    'TITLE_NO_NEW_VIDEOS': "알림",

    # Initialization & Update
    'MSG_INIT_DESC': "필수 구성 요소를 다운로드하고 있습니다...",
    'MSG_INIT_PREPARING': "준비 중...",
    'MSG_INIT_INFO': "잠시만 기다려 주세요. 이 작업은 처음 실행할 때만 수행됩니다.",
    'MSG_INIT_DL_STATUS': "{item} 다운로드 중...",
    'MSG_INIT_COMPLETE': "초기화 완료!",
    'MSG_INIT_STARTING': "YT Downloader를 시작합니다...",
    'MSG_INIT_FAILED': "초기화 실패",
    'ERR_INIT_DOWNLOAD': "다운로드 중 오류가 발생했습니다.",
    'MSG_INIT_CANCELLING': "취소 중...",
    'MSG_INIT_DOWNLOAD_CANCELLED': "다운로드가 취소되었습니다.",



    
    # Init & Update
    'TITLE_INIT': "YT Downloader 초기화",
    'TITLE_INIT_SETUP': "초기 설정",
    'LABEL_LANGUAGE_SELECT': "언어 선택:",
    'MSG_CONFIRM_INIT_DOWNLOAD': "영상 다운로드, 파일 병합, 미디어 검사 및 YouTube 콘텐츠 처리를 위해 필수 구성 요소(yt-dlp, FFmpeg, ffprobe, QuickJS)가 필요합니다.\n\n다운로드하시겠습니까?",
    'BTN_START_SETUP': "시작",
    
    'TITLE_APP_UPDATE': "YT Downloader 업데이트",

    # Startup Dialog
    'TITLE_STARTUP': "YT Downloader 시작 중",
    'MSG_STARTUP_CHECK_EXT': "외부 구성 요소 확인 중...",
    'MSG_STARTUP_CHECK_APP': "앱 업데이트 확인 중...",
    'MSG_STARTUP_OPENING': "앱을 여는 중...",

    # Uninstall
    'TITLE_UNINSTALL': "앱 제거 확인",
    'MSG_UNINSTALL_CONFIRM': "정말로 YT Downloader를 제거하시겠습니까?\n\n다음 항목이 삭제됩니다:\n• 앱 데이터 폴더\n• 실행 파일 (exe)\n\n이 작업은 되돌릴 수 없습니다.",
    'TITLE_UNINSTALL_ERR': "앱 제거 오류",
    'ERR_UNINSTALL_FAIL': "앱 제거 중 오류가 발생했습니다:\n{error}",
    'MSG_DEV_NO_UNINSTALL': "개발자 모드에서는 앱 제거를 지원하지 않습니다.",
    'ERR_UNINSTALL_START': "제거 프로세스를 시작할 수 없습니다.",

    # Update
    'TITLE_UPDATE_CHECK': "업데이트 확인",
    'MSG_UPDATE_AVAILABLE': "새로운 버전이 있습니다!\n\n현재 버전: {current}\n최신 버전: {latest}\n\n지금 업데이트하시겠습니까?",
    'MSG_UPDATE_LATEST': "이미 최신 버전입니다.",
    'MSG_UPDATE_ALL_LATEST': "YT Downloader와 모든 필수 구성 요소가 최신 상태입니다.",
    'MSG_UPDATE_COMPONENT_MISSING': "• {name}: 설치 또는 복구 필요",
    'MSG_UPDATE_RESTART_REQUIRED': "업데이트를 적용하려면 앱을 다시 시작해 주세요.",
    'MSG_UPDATE_RESTART_ACTIVE_TASKS': "활성 다운로드와 대기열의 작업은 앱을 다시 시작할 때 일시 정지되며, 앱이 다시 시작된 뒤 재개할 수 있습니다.",
    'ERR_RESTART_FAILED': "앱을 다시 시작하지 못했습니다. 앱을 수동으로 실행해 주세요.",
    'ERR_UPDATE_CHECK': "업데이트 확인 중 오류가 발생했습니다:\n{error}",
    'MSG_UPDATE_DL': "새 버전을 다운로드하는 중입니다...\n잠시만 기다려 주세요.",
    'MSG_UPDATE_PREPARING': "업데이트 준비 중...",
    'MSG_UPDATE_DL_STATUS': "업데이트 다운로드 중...",
    'MSG_UPDATE_INSTALLING': "업데이트 다운로드가 완료되었습니다. 설치 프로그램을 시작합니다...",
    'MSG_UPDATE_CANCELLED': "업데이트가 취소되었습니다.",
    'ERR_UPDATE_APPLY': "업데이트 적용에 실패했습니다.",
    'ERR_UPDATE_DOWNLOAD': "업데이트 다운로드에 실패했습니다.",
    'MSG_UPDATE_COMPONENTS': "다음 구성 요소에 대한 업데이트가 있습니다:\n\n",
    'MSG_UPDATE_ASK_NOW': "\n지금 업데이트하시겠습니까?",

    # Worker Status
    'WORKER_MSG_CONVERTING': "변환/병합 중",
    'WORKER_MSG_PROCESSING': "처리 중...",
    'WORKER_MSG_COMPLETED': "다운로드 완료",
    'WORKER_MSG_STOPPED': "사용자가 다운로드를 중지함",

    # =========================================================================
    # 6. Toast / Info Messages
    # =========================================================================
    'MSG_READY': "준비됨",
    'MSG_SMART_PASTE': "스마트 붙여넣기: 다운로드를 시작했습니다.",
    'MSG_LICENSE_INFO': "Font Awesome 제공 아이콘 (SIL OFL 1.1)\nMaterial Design Icons (Apache 2.0)\n\n타사 소프트웨어:\n- yt-dlp (The Unlicense)\n- FFmpeg (GPL / LGPL)\n- QuickJS (MIT)\n\n이 소프트웨어는 GNU General Public License v3.0에 따라 배포됩니다.",
    'MSG_DL_ENABLED': "다운로드 활성화됨",
    'MSG_DL_PAUSED': "다운로드 일시 정지됨",
    'MSG_DL_CANCELLED': "다운로드가 취소되었습니다.",
    'MSG_ADDED_QUEUE': "대기열에 추가되었습니다.",
    'MSG_ERROR_COUNT': "오류: {count}개",
    'MSG_COMPLETED_COUNT': "완료: {finished} / {total}",
    'SORT_NEWEST': "최신순",
    'SORT_OLDEST': "오래된 순",
    'SORT_STATUS': "상태순",
    'MSG_NO_NEW_ITEMS': "추가할 새 영상이 없습니다.",
    'MSG_PLAYLIST_EMPTY': "해당 플레이리스트에는 영상이 없습니다.",
    'MSG_PLAYLIST_NO_AVAILABLE_VIDEOS': "해당 플레이리스트에서 가져올 수 있는 영상이 없습니다.",
    'ERR_PLAYLIST_FETCH': "플레이리스트에서 영상을 가져올 수 없습니다.",
    'ERR_NOT_PLAYLIST': "플레이리스트 URL이 아닙니다.",
    'ERR_CANNOT_FETCH_INFO': "정보를 가져올 수 없습니다.",
    'ERR_INVALID_URL': "유효한 영상 URL을 입력해 주세요.",
    'ERR_UNSUPPORTED_URL': "이 URL에서는 다운로드할 수 없습니다.",

    # Loading / Analysis
    'MSG_LOADING': "불러오는 중...",
    'MSG_CHECKING_INFO': "정보 확인 중...",
    'MSG_FETCHING_INFO': "정보를 가져오는 중...",
    'MSG_ANALYZING_PLAYLIST': "플레이리스트를 분석하는 중...",
    'MSG_REGISTERING_PLAYLIST': "플레이리스트의 영상을 대기열에 추가하는 중... ({count})",
    'MSG_ADDED_PLAYLIST': "대기열에 추가된 플레이리스트 영상: {count}개",

    # System / Fatal Errors
    'ERR_MISSING_DEP': "‘{module}’ 필수 라이브러리를 찾을 수 없습니다.",
    'MSG_INSTALL_DEP': "필수 라이브러리를 설치하려면 'pip install -r {file}'을 실행하세요.",
    'TITLE_INIT_FAIL': "초기화 실패",
    'ERR_DL_COMPONENT_FAIL': "필수 구성 요소를 다운로드하지 못했습니다.",
    'MSG_CHECK_NET': "인터넷 연결을 확인하고 다시 시도하세요.",

    'ERR_INIT_GENERIC': "초기화 중 오류가 발생했습니다.",
    'ERR_MODULE_IMPORT': "모듈을 불러올 수 없습니다.",
    'ERR_MODULE_HINT': "오류: {error}\n\n필수 모듈이 누락되었을 수 있습니다.",
    'ERR_START_FAIL': "애플리케이션을 실행할 수 없습니다.",
    'TITLE_FATAL': "치명적인 오류",
    'ERR_FATAL': "치명적인 오류가 발생했습니다.",
    'ERR_YTDLP_MISSING': "yt-dlp를 찾을 수 없습니다",
    'ERR_YTDLP_RESTART': "yt-dlp를 찾을 수 없습니다. 애플리케이션을 다시 시작해 주세요.",


    # =========================================================================
    # 7. Tooltips & Context Menus
    # =========================================================================
    'TOOLTIP_PAUSE': "일시 정지",
    'TOOLTIP_CANCEL': "취소 및 삭제",
    'TOOLTIP_RESUME': "재개",
    'TOOLTIP_REMOVE': "목록에서 제거",
    'TOOLTIP_PLAY': "파일 재생",
    'TOOLTIP_OPEN_FOLDER': "폴더 열기",
    'TOOLTIP_DELETE_FILE': "파일 삭제",
    'TOOLTIP_RETRY': "재시도",
    'TOOLTIP_NORMALIZE': "음량을 -14 LUFS로 정규화합니다.\n변환에 시간이 더 소요됩니다.",
    'TOOLTIP_ACCEL': "파일을 여러 부분으로 나누어 동시에 다운로드합니다.\n다운로드 속도가 향상될 수 있습니다.\n(활성화하면 최대 동시 다운로드 수가 1로 고정됩니다)",
    'TOOLTIP_COMPATIBILITY': "출력 형식을 MP4 또는 MP3로 제한합니다.\nMP4 영상은 폭넓은 기기 호환성을 위해 H.264/AAC로 인코딩합니다.",

    'MENU_PLAY': "재생",
    'MENU_OPEN_FOLDER': "폴더 열기",
    'MENU_COPY_URL': "URL 복사",
    'MENU_PAUSE': "일시 정지",
    'MENU_RESUME': "재개",
    'MENU_RETRY': "재시도",
    'MENU_DELETE_FILE': "파일 삭제",
    'MENU_REMOVE': "목록에서 제거",
    'MENU_REMOVE_COMPLETED': "완료된 항목을 목록에서 제거",

    # =========================================================================
    # 8. Task Actions & Confirmations
    # =========================================================================
    'ERR_TASK_NOT_FOUND': "작업을 찾을 수 없습니다.",
    'ERR_NO_FILE_PATH': "파일 경로가 저장되지 않았습니다.",
    'ERR_EXECUTE_FILE': "파일을 실행할 수 없습니다:\n{error}",
    'ERR_FILE_NOT_FOUND_PATH': "파일을 찾을 수 없습니다.\n\n경로: {path}",
    'ERR_OPEN_FOLDER': "폴더를 열 수 없습니다: {error}",
    
    'TITLE_DELETE_CONFIRM': "삭제 확인",
    'MSG_DELETE_CONFIRM': "정말로 이 파일을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
    'MSG_DELETE_CONFIRM_MANY': "정말로 {count}개의 파일을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.",
    
    'TITLE_DELETE_FAILED': "삭제 실패",
    'ERR_DELETE_PERMISSION': "파일이 사용 중이거나 권한이 없습니다:\n{path}",
    'ERR_DELETE_ERROR': "파일을 삭제할 수 없습니다:\n{error}",
    
    'TITLE_REMOVE_CONFIRM': "제거 확인",
    'MSG_REMOVE_CONFIRM': "선택한 항목을 목록에서 제거하시겠습니까? ({count}개)",
    'MSG_REMOVE_COMPLETED_CONFIRM': "완료된 항목을 목록에서 제거하시겠습니까? ({count}개)",

    # =========================================================================
    # 9. Constants & Lists
    # =========================================================================
    'TPL_VIDEO_TITLE': "영상 ID: {video_id}",

    # COOKIES_BROWSER_DISPLAY removed (replaced by in-app login)
}
