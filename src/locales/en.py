"""
English string definitions
"""
STRINGS = {
    # Settings dialog
    'SETTINGS_DIALOG_TITLE': "Settings",
    'SETTINGS_CLOSE_BUTTON_TEXT': "✕",
    'SETTINGS_SECTION_SAVE_LOCATION': "Save Location",
    'SETTINGS_BROWSE_BUTTON_TEXT': "Browse",
    'SETTINGS_SECTION_QUALITY_FORMAT': "Quality & Format",
    'SETTINGS_LABEL_VIDEO_QUALITY': "Video Quality:",
    'SETTINGS_LABEL_AUDIO_QUALITY': "Audio Quality:",
    'SETTINGS_LABEL_FORMAT': "Format:",
    'SETTINGS_SECTION_GENERAL': "General Settings",
    'SETTINGS_LABEL_MAX_DOWNLOADS': "Max Downloads:",
    'SETTINGS_SECTION_ADVANCED': "Advanced Features",
    'SETTINGS_CHECKBOX_NORMALIZE': "Loudness Normalization",
    'SETTINGS_CHECKBOX_ACCELERATION': "Download Acceleration (Multi-thread)",
    'SETTINGS_BUTTON_CANCEL': "Cancel",
    'SETTINGS_BUTTON_SAVE': "Save",
    'SETTINGS_FOLDER_DIALOG_TITLE': "Select Download Folder",
    'SETTINGS_ERROR_TITLE': "Error",
    'SETTINGS_ERROR_NO_FOLDER': "Please select a download folder.",
    'SETTINGS_ERROR_CANNOT_CREATE_FOLDER': "Cannot create folder:\n{error}",
    'SETTINGS_ERROR_INVALID_FOLDER': "The selected path is not a valid folder.",
    
    # Main window
    'APP_TITLE': "YT Downloader",
    'TITLE_BAR_MINIMIZE_BUTTON_TEXT': "─",
    'TITLE_BAR_CLOSE_BUTTON_TEXT': "✕",
    'URL_INPUT_PLACEHOLDER': "Enter YouTube link",
    'DOWNLOAD_BUTTON_TEXT': "Download",
    'SETTINGS_BUTTON_TEXT': "⚙",
    'EMPTY_STATE_MESSAGE': "No videos to download.\nEnter a URL at the top to get started.",
    'STATUS_BAR_DEFAULT_TEXT': "Ready",
    
    # Task status
    'STATUS_TEXT_WAITING': 'Waiting',
    'STATUS_TEXT_DOWNLOADING': 'Downloading',
    'STATUS_TEXT_PAUSED': 'Paused',
    'STATUS_TEXT_IN_PROGRESS': 'In Progress',
    'STATUS_TEXT_WAITING_DOTS': 'Waiting...',
    'STATUS_TEXT_PAUSED_SAVED': 'Paused (Saved)',
    'STATUS_TEXT_PREVIOUS_FAILED': 'Previous Task Failed',
    
    # Messages
    'MSG_READY': "Ready",
    'MSG_SMART_PASTE_STARTED': "Smart Paste: Download started",
    'MSG_DOWNLOAD_ENABLED': "Download enabled",
    'MSG_DOWNLOAD_PAUSED': "Download paused",
    'MSG_DOWNLOAD_CANCELLED': "Download cancelled.",
    'MSG_ADDED_TO_QUEUE': "Added to queue.",
    'MSG_PLAYLIST_ANALYZING': "Analyzing playlist...",
    'MSG_PLAYLIST_REGISTERING': "Registering {count} videos from playlist...",
    'MSG_PLAYLIST_ADDED': "{count} videos from playlist added to queue.",
    'MSG_ERROR_COUNT': "Errors: {count}",
    'MSG_COMPLETED_COUNT': "Completed: {finished} / {total}",
    'MSG_NO_NEW_VIDEOS': "No new videos to add.",
    'MSG_PLAYLIST_FETCH_ERROR': "Could not fetch videos from playlist.",
    'MSG_DOWNLOAD_COMPLETE': "Complete",
    'MSG_NOT_PLAYLIST_URL': "Not a playlist URL.",
    'MSG_CANNOT_FETCH_INFO': "Could not fetch information.",
    
    # Dialogs
    'DIALOG_DUPLICATE_VIDEOS_TITLE': "Duplicate Videos",
    'DIALOG_DUPLICATE_VIDEOS_MESSAGE': "{duplicate} out of {total} videos in playlist are already downloaded.\nExclude duplicate videos?",
    'DIALOG_RESUME_DOWNLOAD_TITLE': "Resume Download",
    'DIALOG_RESUME_DOWNLOAD_MESSAGE': "Resume previously downloading task?",
    'DIALOG_NO_NEW_VIDEOS_TITLE': "Notification",
    
    # Duplicate download
    'DUPLICATE_CHECK_TITLE': "Duplicate Download Check",
    'DUPLICATE_MSG_ALREADY_DOWNLOADED': "Video already downloaded in '{format}' format.\n",
    'DUPLICATE_MSG_IN_QUEUE': "(Task currently in {status} state)\n",
    'DUPLICATE_MSG_ASK_OVERWRITE': "\nDownload again (overwrite)?",
    
    # Playlist
    'PLAYLIST_VIDEO_TITLE_TEMPLATE': "Video ID: {video_id}",
    
    # Warning
    'WARNING_PLAYLIST_WORKER_TIMEOUT': "Playlist worker did not terminate within time limit.",
}
