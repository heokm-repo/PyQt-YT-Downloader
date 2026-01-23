"""
한국어 문자열 정의
"""
STRINGS = {
    # 설정 다이얼로그
    'SETTINGS_DIALOG_TITLE': "설정",
    'SETTINGS_CLOSE_BUTTON_TEXT': "✕",
    'SETTINGS_SECTION_SAVE_LOCATION': "저장 위치",
    'SETTINGS_BROWSE_BUTTON_TEXT': "찾아보기",
    'SETTINGS_SECTION_QUALITY_FORMAT': "품질 및 포맷",
    'SETTINGS_LABEL_VIDEO_QUALITY': "화질:",
    'SETTINGS_LABEL_AUDIO_QUALITY': "음질:",
    'SETTINGS_LABEL_FORMAT': "포맷:",
    'SETTINGS_SECTION_GENERAL': "일반 설정",
    'SETTINGS_LABEL_MAX_DOWNLOADS': "최대 다운로드 수:",
    'SETTINGS_SECTION_ADVANCED': "고급 기능",
    'SETTINGS_CHECKBOX_NORMALIZE': "음량 평준화 (Loudness Normalization)",
    'SETTINGS_CHECKBOX_ACCELERATION': "다운로드 가속 (멀티 스레드)",
    'SETTINGS_BUTTON_CANCEL': "취소",
    'SETTINGS_BUTTON_SAVE': "저장",
    'SETTINGS_FOLDER_DIALOG_TITLE': "다운로드 폴더 선택",
    'SETTINGS_ERROR_TITLE': "오류",
    'SETTINGS_ERROR_NO_FOLDER': "다운로드 폴더를 선택해주세요.",
    'SETTINGS_ERROR_CANNOT_CREATE_FOLDER': "폴더를 생성할 수 없습니다:\n{error}",
    'SETTINGS_ERROR_INVALID_FOLDER': "선택한 경로가 유효한 폴더가 아닙니다.",
    
    # 메인 윈도우
    'APP_TITLE': "YT Downloader",
    'TITLE_BAR_MINIMIZE_BUTTON_TEXT': "─",
    'TITLE_BAR_CLOSE_BUTTON_TEXT': "✕",
    'URL_INPUT_PLACEHOLDER': "YouTube 링크 입력",
    'DOWNLOAD_BUTTON_TEXT': "다운로드",
    'SETTINGS_BUTTON_TEXT': "⚙",
    'EMPTY_STATE_MESSAGE': "다운로드할 영상이 없습니다.\n상단에 URL을 입력하여 시작하세요.",
    'STATUS_BAR_DEFAULT_TEXT': "준비됨",
    
    # 작업 상태
    'STATUS_TEXT_WAITING': '대기 중',
    'STATUS_TEXT_DOWNLOADING': '다운로드 중',
    'STATUS_TEXT_PAUSED': '일시정지됨',
    'STATUS_TEXT_IN_PROGRESS': '진행 중',
    'STATUS_TEXT_WAITING_DOTS': '대기 중...',
    'STATUS_TEXT_PAUSED_SAVED': '일시정지됨 (저장됨)',
    'STATUS_TEXT_PREVIOUS_FAILED': '이전 작업 실패',
    
    # 메시지
    'MSG_READY': "준비됨",
    'MSG_SMART_PASTE_STARTED': "스마트 붙여넣기: 다운로드 시작됨",
    'MSG_DOWNLOAD_ENABLED': "다운로드 활성화됨",
    'MSG_DOWNLOAD_PAUSED': "다운로드 일시정지됨",
    'MSG_DOWNLOAD_CANCELLED': "다운로드가 취소되었습니다.",
    'MSG_ADDED_TO_QUEUE': "대기열에 추가되었습니다.",
    'MSG_PLAYLIST_ANALYZING': "플레이리스트를 분석하는 중...",
    'MSG_PLAYLIST_REGISTERING': "플레이리스트 {count}개 영상 등록 중...",
    'MSG_PLAYLIST_ADDED': "플레이리스트 {count}개 영상이 대기열에 추가되었습니다.",
    'MSG_ERROR_COUNT': "오류: {count}개",
    'MSG_COMPLETED_COUNT': "완료: {finished} / {total}",
    'MSG_NO_NEW_VIDEOS': "추가할 새 영상이 없습니다.",
    'MSG_PLAYLIST_FETCH_ERROR': "플레이리스트에서 영상을 가져올 수 없습니다.",
    'MSG_DOWNLOAD_COMPLETE': "완료",
    'MSG_NOT_PLAYLIST_URL': "플레이리스트 URL이 아닙니다.",
    'MSG_CANNOT_FETCH_INFO': "정보를 가져올 수 없습니다.",
    
    # 다이얼로그
    'DIALOG_DUPLICATE_VIDEOS_TITLE': "중복 영상 확인",
    'DIALOG_DUPLICATE_VIDEOS_MESSAGE': "플레이리스트 {total}개 중 {duplicate}개는 이미 다운로드한 영상입니다.\n중복된 영상을 제외할까요?",
    'DIALOG_RESUME_DOWNLOAD_TITLE': "다운로드 재개",
    'DIALOG_RESUME_DOWNLOAD_MESSAGE': "이전에 다운로드중인 작업을 재개하시겠습니까?",
    'DIALOG_NO_NEW_VIDEOS_TITLE': "알림",
    
    # 중복 다운로드
    'DUPLICATE_CHECK_TITLE': "중복 다운로드 확인",
    'DUPLICATE_MSG_ALREADY_DOWNLOADED': "이미 '{format}' 포맷으로 다운로드된 영상입니다.\n",
    'DUPLICATE_MSG_IN_QUEUE': "(현재 {status} 상태인 작업이 있습니다)\n",
    'DUPLICATE_MSG_ASK_OVERWRITE': "\n다시 다운로드(덮어쓰기) 하시겠습니까?",
    
    # 플레이리스트
    'PLAYLIST_VIDEO_TITLE_TEMPLATE': "영상 ID: {video_id}",
    
    # 경고
    'WARNING_PLAYLIST_WORKER_TIMEOUT': "플레이리스트 워커가 시간 내에 종료되지 않았습니다.",
}
