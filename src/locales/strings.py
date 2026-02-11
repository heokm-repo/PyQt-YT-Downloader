from . import get_string

class Strings:
    """
    Singleton class for managing UI strings dynamically.
    @property is used to reflect language changes immediately.
    """

    # =========================================================================
    # 1. Common / Global
    # =========================================================================
    @property
    def BTN_OK(self):       return get_string('BTN_OK', "OK")
    @property
    def BTN_YES(self):      return get_string('BTN_YES', "Yes")
    @property
    def BTN_NO(self):       return get_string('BTN_NO', "No")
    @property
    def BTN_CLOSE(self):    return get_string('BTN_CLOSE', "Close")
    @property
    def BTN_CANCEL(self):   return get_string('BTN_CANCEL', "Cancel")
    @property
    def BTN_SAVE(self):     return get_string('BTN_SAVE', "Save")
    
    @property
    def TITLE_INFO(self):     return get_string('TITLE_INFO', "Info")
    @property
    def TITLE_WARNING(self):  return get_string('TITLE_WARNING', "Warning")
    @property
    def TITLE_ERROR(self):    return get_string('TITLE_ERROR', "Error")
    @property
    def TITLE_CONFIRM(self):  return get_string('TITLE_CONFIRM', "Confirm")

    # =========================================================================
    # 2. Main Window
    # =========================================================================
    @property
    def MAIN_URL_PLACEHOLDER(self): return get_string('MAIN_URL_PLACEHOLDER', "Enter YouTube link")
    @property
    def BTN_DOWNLOAD(self):         return get_string('BTN_DOWNLOAD', "Download")
    @property
    def MAIN_EMPTY_STATE(self):     return get_string('MAIN_EMPTY_STATE', "No videos to download.\nEnter a URL at the top to get started.")
    @property
    def MAIN_STATUS_READY(self):    return get_string('MAIN_STATUS_READY', "Ready")

    # =========================================================================
    # 3. Settings Dialog
    # =========================================================================
    @property
    def TITLE_SETTINGS(self): return get_string('TITLE_SETTINGS', "Settings")

    # Section: Save Location
    @property
    def TITLE_FOLDER_SELECT(self):   return get_string('TITLE_FOLDER_SELECT', "Select Download Folder")
    @property
    def SETTINGS_SEC_LOCATION(self): return get_string('SETTINGS_SEC_LOCATION', "Save Location")
    @property
    def SETTINGS_BTN_BROWSE(self):   return get_string('SETTINGS_BTN_BROWSE', "Browse")

    # Section: Quality & Format
    @property
    def SETTINGS_SEC_QUALITY(self):    return get_string('SETTINGS_SEC_QUALITY', "Quality & Format")
    @property
    def SETTINGS_LABEL_VIDEO(self):    return get_string('SETTINGS_LABEL_VIDEO', "Video Quality:")
    @property
    def SETTINGS_LABEL_AUDIO(self):    return get_string('SETTINGS_LABEL_AUDIO', "Audio Quality:")
    @property
    def SETTINGS_LABEL_FORMAT(self):   return get_string('SETTINGS_LABEL_FORMAT', "Format:")
    @property
    def SETTINGS_HEADER_VIDEO(self):   return get_string('SETTINGS_HEADER_VIDEO', "=== VIDEO ===")
    @property
    def SETTINGS_HEADER_AUDIO(self):   return get_string('SETTINGS_HEADER_AUDIO', "=== AUDIO ===")

    # Section: General Settings
    @property
    def SETTINGS_SEC_GENERAL(self):     return get_string('SETTINGS_SEC_GENERAL', "General Settings")
    @property
    def SETTINGS_LABEL_MAX_DL(self):    return get_string('SETTINGS_LABEL_MAX_DL', "Max Downloads:")
    @property
    def SETTINGS_LABEL_LANGUAGE(self):  return get_string('SETTINGS_LABEL_LANGUAGE', "Language:")
    
    # Section: Advanced Features
    @property
    def SETTINGS_SEC_ADVANCED(self):    return get_string('SETTINGS_SEC_ADVANCED', "Advanced Features")
    @property
    def SETTINGS_CHK_NORMALIZE(self):   return get_string('SETTINGS_CHK_NORMALIZE', "Loudness Normalization")
    @property
    def SETTINGS_CHK_ACCEL(self):       return get_string('SETTINGS_CHK_ACCEL', "Download Acceleration (Multi-thread)")
    @property
    def SETTINGS_LABEL_COOKIES(self):   return get_string('SETTINGS_LABEL_COOKIES', "Cookies Integration:")

    # Section: App Management
    @property
    def SETTINGS_SEC_APP_MANAGE(self):   return get_string('SETTINGS_SEC_APP_MANAGE', "App Management")
    @property
    def SETTINGS_LABEL_VERSION(self):    return get_string('SETTINGS_LABEL_VERSION', "Current Version:")
    @property
    def SETTINGS_BTN_CHECK_UPDATE(self): return get_string('SETTINGS_BTN_CHECK_UPDATE', "Check for Updates")
    @property
    def SETTINGS_BTN_UNINSTALL(self):    return get_string('SETTINGS_BTN_UNINSTALL', "Uninstall App")

    # Settings Errors
    @property
    def ERR_SETTINGS_NO_FOLDER(self):      return get_string('ERR_SETTINGS_NO_FOLDER', "Please select a download folder.")
    @property
    def ERR_SETTINGS_CREATE_FOLDER(self):  return get_string('ERR_SETTINGS_CREATE_FOLDER', "Cannot create folder:\n{error}")
    @property
    def ERR_SETTINGS_INVALID_FOLDER(self): return get_string('ERR_SETTINGS_INVALID_FOLDER', "The selected path is not a valid folder.")

    # =========================================================================
    # 4. Status Messages
    # =========================================================================
    @property
    def STATUS_WAITING(self):           return get_string('STATUS_WAITING', 'Waiting')
    @property
    def STATUS_WAITING_DOTS(self):      return get_string('STATUS_WAITING_DOTS', 'Waiting...')
    @property
    def STATUS_DOWNLOADING(self):       return get_string('STATUS_DOWNLOADING', 'Downloading')
    @property
    def STATUS_DOWNLOADING_DOTS(self):  return get_string('STATUS_DOWNLOADING_DOTS', "Downloading...")
    @property
    def STATUS_DOWNLOADING_SPEED(self): return get_string('STATUS_DOWNLOADING_SPEED', "Downloading ({speed})")
    
    @property
    def STATUS_PAUSED(self):        return get_string('STATUS_PAUSED', 'Paused')
    @property
    def STATUS_PAUSED_SAVED(self):  return get_string('STATUS_PAUSED_SAVED', 'Paused (Saved)')
    @property
    def STATUS_IN_PROGRESS(self):   return get_string('STATUS_IN_PROGRESS', 'In Progress')
    @property
    def STATUS_PREV_FAILED(self):   return get_string('STATUS_PREV_FAILED', 'Previous Task Failed')
    
    @property
    def STATUS_CONVERTING(self):    return get_string('STATUS_CONVERTING', "Converting...")
    @property
    def STATUS_LOADING(self):       return get_string('STATUS_LOADING', "Loading...")
    @property
    def STATUS_COMPLETED(self):     return get_string('STATUS_COMPLETED', "Completed")
    @property
    def STATUS_FAILED_FMT(self):    return get_string('STATUS_FAILED_FMT', "Failed: {message}")
    @property
    def STATUS_PREPARING(self):     return get_string('STATUS_PREPARING', "Preparing download...")
    @property
    def STATUS_NO_IMAGE(self):      return get_string('STATUS_NO_IMAGE', "No Image")

    # Worker Status
    @property
    def WORKER_MSG_CONVERTING(self): return get_string('WORKER_MSG_CONVERTING', "Converting/Merging")
    @property
    def WORKER_MSG_PROCESSING(self): return get_string('WORKER_MSG_PROCESSING', "Processing...")
    @property
    def WORKER_MSG_COMPLETE(self):   return get_string('WORKER_MSG_COMPLETE', "Download Complete")
    @property
    def WORKER_MSG_STOPPED(self):    return get_string('WORKER_MSG_STOPPED', "Download stopped by user")

    # =========================================================================
    # 5. Dialogs & Popups
    # =========================================================================
    
    # URL Choice
    @property
    def TITLE_CHOICE(self):          return get_string('TITLE_CHOICE', "Download Option")
    @property
    def MSG_CHOICE_PLAYLIST(self):   return get_string('MSG_CHOICE_PLAYLIST', "This URL contains both video and playlist information.\n\nHow would you like to download?")
    @property
    def BTN_CHOICE_ALL(self):        return get_string('BTN_CHOICE_ALL', "Entire Playlist")
    @property
    def BTN_CHOICE_VIDEO(self):      return get_string('BTN_CHOICE_VIDEO', "Video Only")

    # Duplicate / Resume
    @property
    def TITLE_DUPLICATE(self):       return get_string('TITLE_DUPLICATE', "Duplicate Videos")
    @property
    def MSG_DUPLICATE_FOUND(self):   return get_string('MSG_DUPLICATE_FOUND', "{duplicate} out of {total} videos in playlist are already downloaded.\nExclude duplicate videos?")
    @property
    def MSG_DUPLICATE_CHECK(self):   return get_string('MSG_DUPLICATE_CHECK', "Duplicate Download Check")
    @property
    def MSG_DUP_ALREADY_DONE(self):  return get_string('MSG_DUP_ALREADY_DONE', "Video already downloaded in '{format}' format.\n")
    @property
    def MSG_DUP_IN_QUEUE(self):      return get_string('MSG_DUP_IN_QUEUE', "(Task currently in {status} state)\n")
    @property
    def MSG_DUP_ASK_OVERWRITE(self): return get_string('MSG_DUP_ASK_OVERWRITE', "\nDownload again (overwrite)?")
    
    @property
    def TITLE_RESUME(self):          return get_string('TITLE_RESUME', "Resume Download")
    @property
    def MSG_RESUME_CONFIRM(self):    return get_string('MSG_RESUME_CONFIRM', "Resume previously downloading task?")
    @property
    def TITLE_NO_NEW_VIDEOS(self):   return get_string('TITLE_NO_NEW_VIDEOS', "Notification")

    # Initialization & Update
    @property
    def TITLE_INIT(self):           return get_string('TITLE_INIT', "YT Downloader Initialization")
    @property
    def TITLE_APP_UPDATE(self):     return get_string('TITLE_APP_UPDATE', "YT Downloader Update")
    @property
    def MSG_INIT_TITLE(self):       return get_string('MSG_INIT_TITLE', "Initializing YT Downloader...")
    @property
    def MSG_INIT_DESC(self):        return get_string('MSG_INIT_DESC', "Downloading required components...")
    @property
    def MSG_INIT_PREPARING(self):   return get_string('MSG_INIT_PREPARING', "Preparing...")
    @property
    def MSG_INIT_INFO(self):        return get_string('MSG_INIT_INFO', "Please wait. This process runs only on the first launch.")
    @property
    def MSG_INIT_DL_STATUS(self):   return get_string('MSG_INIT_DL_STATUS', "Downloading {item}...")
    @property
    def MSG_INIT_COMPLETE(self):    return get_string('MSG_INIT_COMPLETE', "Initialization Complete!")
    @property
    def MSG_INIT_STARTING(self):    return get_string('MSG_INIT_STARTING', "Starting YT Downloader...")
    @property
    def MSG_INIT_FAILED(self):      return get_string('MSG_INIT_FAILED', "Initialization Failed")
    @property
    def ERR_INIT_DOWNLOAD(self):    return get_string('ERR_INIT_DOWNLOAD', "An error occurred during download.")
    @property
    def MSG_CONFIRM_INIT_DOWNLOAD(self): return get_string('MSG_CONFIRM_INIT_DOWNLOAD', "Essential components (yt-dlp, FFmpeg) are required for video downloading and merging.\n\nDo you want to download them?")
    @property
    def MSG_DOWNLOAD_COMPONENT_FAIL(self): return get_string('MSG_DOWNLOAD_COMPONENT_FAIL', "Required components failed to download.")
    @property
    def MSG_CHECK_INTERNET(self):   return get_string('MSG_CHECK_INTERNET', "Please check your internet connection.")

    # Uninstall
    @property
    def TITLE_UNINSTALL(self):       return get_string('TITLE_UNINSTALL', "Confirm Uninstall")
    @property
    def MSG_UNINSTALL_CONFIRM(self): return get_string('MSG_UNINSTALL_CONFIRM', "Are you sure you want to uninstall YT Downloader?\n\nThe following will be deleted:\n• App data folder\n• Executable file (exe)\n\nThis action cannot be undone.")
    @property
    def TITLE_UNINSTALL_ERR(self):   return get_string('TITLE_UNINSTALL_ERR', "Uninstall Error")
    @property
    def ERR_UNINSTALL_FAIL(self):    return get_string('ERR_UNINSTALL_FAIL', "An error occurred while uninstalling:\n{error}")
    @property
    def MSG_DEV_NO_UNINSTALL(self):  return get_string('MSG_DEV_NO_UNINSTALL', "App uninstall is not supported in developer mode.")
    @property
    def ERR_UNINSTALL_START(self):   return get_string('ERR_UNINSTALL_START', "Could not start the uninstallation process.")

    # Update
    @property
    def TITLE_UPDATE_CHECK(self):     return get_string('TITLE_UPDATE_CHECK', "Check for Updates")
    @property
    def MSG_UPDATE_AVAILABLE(self):   return get_string('MSG_UPDATE_AVAILABLE', "A new version is available!\n\nCurrent version: {current}\nLatest version: {latest}\n\nWould you like to update now?")
    @property
    def MSG_UPDATE_LATEST(self):      return get_string('MSG_UPDATE_LATEST', "You are already using the latest version.")
    @property
    def ERR_UPDATE_CHECK(self):       return get_string('ERR_UPDATE_CHECK', "An error occurred while checking for updates:\n{error}")
    @property
    def TITLE_UPDATE_DL(self):        return get_string('TITLE_UPDATE_DL', "Update in Progress")
    @property
    def MSG_UPDATE_DL(self):          return get_string('MSG_UPDATE_DL', "Downloading the new version...\nPlease wait.")
    @property
    def ERR_UPDATE_APPLY(self):       return get_string('ERR_UPDATE_APPLY', "Failed to apply the update.")
    @property
    def ERR_UPDATE_DOWNLOAD(self):    return get_string('ERR_UPDATE_DOWNLOAD', "Failed to download the update.")
    @property
    def MSG_UPDATE_COMPONENTS(self):  return get_string('MSG_UPDATE_COMPONENTS', "Updates available for the following components:\n\n")
    @property
    def MSG_UPDATE_ASK_NOW(self):     return get_string('MSG_UPDATE_ASK_NOW', "\nUpdate now?")

    # =========================================================================
    # 6. Toast / Info Messages
    # =========================================================================
    @property
    def MSG_READY(self):               return get_string('MSG_READY', "Ready")
    @property
    def MSG_SMART_PASTE(self):         return get_string('MSG_SMART_PASTE', "Smart Paste: Download started")
    @property
    def MSG_DL_ENABLED(self):          return get_string('MSG_DL_ENABLED', "Download enabled")
    @property
    def MSG_DL_PAUSED(self):           return get_string('MSG_DL_PAUSED', "Download paused")
    @property
    def MSG_DL_CANCELLED(self):        return get_string('MSG_DL_CANCELLED', "Download cancelled.")
    @property
    def MSG_ADDED_QUEUE(self):         return get_string('MSG_ADDED_QUEUE', "Added to queue.")
    @property
    def MSG_ERROR_COUNT(self):         return get_string('MSG_ERROR_COUNT', "Errors: {count}")
    @property
    def MSG_COMPLETED_COUNT(self):     return get_string('MSG_COMPLETED_COUNT', "Completed: {finished} / {total}")
    @property
    def MSG_NO_NEW_ITEMS(self):        return get_string('MSG_NO_NEW_ITEMS', "No new videos to add.")
    @property
    def MSG_ALL_DONE(self):            return get_string('MSG_ALL_DONE', "Complete")
    @property
    def ERR_PLAYLIST_FETCH(self):      return get_string('ERR_PLAYLIST_FETCH', "Could not fetch videos from playlist.")
    @property
    def ERR_NOT_PLAYLIST(self):        return get_string('ERR_NOT_PLAYLIST', "Not a playlist URL.")
    @property
    def ERR_CANNOT_FETCH_INFO(self):   return get_string('ERR_CANNOT_FETCH_INFO', "Could not fetch information.")
    @property
    def ERR_INVALID_URL(self):         return get_string('ERR_INVALID_URL', "Please enter a valid YouTube URL.")

    # Loading / Analysis
    @property
    def MSG_LOADING(self):             return get_string('MSG_LOADING', "Loading...")
    @property
    def MSG_CHECKING_INFO(self):       return get_string('MSG_CHECKING_INFO', "Checking info...")
    @property
    def MSG_FETCHING_INFO(self):       return get_string('MSG_FETCHING_INFO', "Fetching info...")
    @property
    def MSG_ANALYZING_PLAYLIST(self):  return get_string('MSG_ANALYZING_PLAYLIST', "Analyzing playlist...")
    @property
    def MSG_REGISTERING_PLAYLIST(self):return get_string('MSG_REGISTERING_PLAYLIST', "Registering {count} videos from playlist...")
    @property
    def MSG_ADDED_PLAYLIST(self):      return get_string('MSG_ADDED_PLAYLIST', "{count} videos from playlist added to queue.")

    # System / Fatal Errors
    @property
    def ERR_MISSING_DEP(self):         return get_string('ERR_MISSING_DEP', "Required library '{module}' not found.")
    @property
    def MSG_INSTALL_DEP(self):         return get_string('MSG_INSTALL_DEP', "Please run 'pip install -r {file}' to install required libraries.")
    @property
    def TITLE_INIT_FAIL(self):         return get_string('TITLE_INIT_FAIL', "Initialization Failed")
    @property
    def ERR_DL_COMPONENT_FAIL(self):   return get_string('ERR_DL_COMPONENT_FAIL', "Failed to download required components.")
    @property
    def MSG_CHECK_NET(self):           return get_string('MSG_CHECK_NET', "Please check your internet connection and try again.")
    @property
    def TITLE_INIT_ERR(self):          return get_string('TITLE_INIT_ERR', "Initialization Error")
    @property
    def ERR_INIT_GENERIC(self):        return get_string('ERR_INIT_GENERIC', "An error occurred during initialization.")
    @property
    def ERR_MODULE_IMPORT(self):       return get_string('ERR_MODULE_IMPORT', "Could not import module.")
    @property
    def ERR_MODULE_HINT(self):         return get_string('ERR_MODULE_HINT', "Error: {error}\n\nA required module might be missing.")
    @property
    def ERR_START_FAIL(self):          return get_string('ERR_START_FAIL', "Could not start the application.")
    @property
    def TITLE_FATAL(self):             return get_string('TITLE_FATAL', "Fatal Error")
    @property
    def ERR_FATAL(self):               return get_string('ERR_FATAL', "A fatal error occurred.")
    @property
    def ERR_YTDLP_MISSING(self):       return get_string('ERR_YTDLP_MISSING', "yt-dlp not found")
    @property
    def ERR_YTDLP_RESTART(self):       return get_string('ERR_YTDLP_RESTART', "yt-dlp not found. Please restart the application.")
    @property
    def WARN_WORKER_TIMEOUT(self):     return get_string('WARN_WORKER_TIMEOUT', "Playlist worker did not terminate within time limit.")

    # =========================================================================
    # 7. Tooltips & Context Menus
    # =========================================================================
    @property
    def TOOLTIP_PAUSE(self):        return get_string('TOOLTIP_PAUSE', "Pause")
    @property
    def TOOLTIP_CANCEL(self):       return get_string('TOOLTIP_CANCEL', "Cancel and Delete")
    @property
    def TOOLTIP_RESUME(self):       return get_string('TOOLTIP_RESUME', "Resume")
    @property
    def TOOLTIP_REMOVE(self):       return get_string('TOOLTIP_REMOVE', "Remove from list")
    @property
    def TOOLTIP_PLAY(self):         return get_string('TOOLTIP_PLAY', "Play file")
    @property
    def TOOLTIP_OPEN_FOLDER(self):  return get_string('TOOLTIP_OPEN_FOLDER', "Open Folder")
    @property
    def TOOLTIP_DELETE_FILE(self):  return get_string('TOOLTIP_DELETE_FILE', "Delete File")
    @property
    def TOOLTIP_RETRY(self):        return get_string('TOOLTIP_RETRY', "Retry")
    @property
    def TOOLTIP_NORMALIZE(self):    return get_string('TOOLTIP_NORMALIZE', "Standardize volume to broadcast standard (-14 LUFS).\nConversion takes a bit longer.")
    @property
    def TOOLTIP_ACCEL(self):        return get_string('TOOLTIP_ACCEL', "Download file in multiple parts concurrently.\nIncreases download speed.\n(Max downloads fixed to 1 when selected)")

    # Context Menus (Translated Defaults)
    @property
    def MENU_PLAY(self):         return get_string('MENU_PLAY', "▶ Play")
    @property
    def MENU_OPEN_FOLDER(self):  return get_string('MENU_OPEN_FOLDER', "📂 Open Folder")
    @property
    def MENU_COPY_URL(self):     return get_string('MENU_COPY_URL', "🔗 Copy URL")
    @property
    def MENU_PAUSE(self):        return get_string('MENU_PAUSE', "⏸ Pause")
    @property
    def MENU_RESUME(self):       return get_string('MENU_RESUME', "▶ Resume")
    @property
    def MENU_RETRY(self):        return get_string('MENU_RETRY', "↻ Retry")
    @property
    def MENU_DELETE_FILE(self):  return get_string('MENU_DELETE_FILE', "🗑️ Delete File")
    @property
    def MENU_REMOVE(self):       return get_string('MENU_REMOVE', "❌ Remove from List")

    # =========================================================================
    # 8. Task Actions & Confirmations
    # =========================================================================
    @property
    def ERR_TASK_NOT_FOUND(self):       return get_string('ERR_TASK_NOT_FOUND', "Task not found.")
    @property
    def ERR_NO_FILE_PATH(self):         return get_string('ERR_NO_FILE_PATH', "File path not saved.")
    @property
    def ERR_EXECUTE_FILE(self):         return get_string('ERR_EXECUTE_FILE', "Cannot execute file:\n{error}")
    @property
    def ERR_FILE_NOT_FOUND_PATH(self):  return get_string('ERR_FILE_NOT_FOUND_PATH', "File not found.\n\nPath: {path}")
    @property
    def ERR_OPEN_FOLDER(self):          return get_string('ERR_OPEN_FOLDER', "Cannot open folder: {error}")
    
    @property
    def TITLE_DELETE_CONFIRM(self):     return get_string('TITLE_DELETE_CONFIRM', "Confirm Delete")
    @property
    def MSG_DELETE_CONFIRM(self):       return get_string('MSG_DELETE_CONFIRM', "Are you sure you want to delete this file?\nThis action cannot be undone.")
    @property
    def MSG_DELETE_CONFIRM_MANY(self):  return get_string('MSG_DELETE_CONFIRM_MANY', "Are you sure you want to delete {count} files?\nThis action cannot be undone.")
    
    @property
    def TITLE_DELETE_FAILED(self):      return get_string('TITLE_DELETE_FAILED', "Delete Failed")
    @property
    def ERR_DELETE_PERMISSION(self):    return get_string('ERR_DELETE_PERMISSION', "File is in use or permission denied:\n{path}")
    @property
    def ERR_DELETE_ERROR(self):         return get_string('ERR_DELETE_ERROR', "Cannot delete file:\n{error}")
    
    @property
    def TITLE_REMOVE_CONFIRM(self):     return get_string('TITLE_REMOVE_CONFIRM', "Confirm Remove")
    @property
    def MSG_REMOVE_CONFIRM(self):       return get_string('MSG_REMOVE_CONFIRM', "Remove {count} items from the list?")

    # =========================================================================
    # 9. Constants & Lists
    # =========================================================================
    @property
    def TPL_VIDEO_TITLE(self): return get_string('TPL_VIDEO_TITLE', "Video ID: {video_id}")

    @property
    def COOKIES_BROWSER_VALUES(self): return ['', 'chrome', 'edge', 'firefox', 'whale']

    @property
    def COOKIES_BROWSER_DISPLAY(self):
        """Returns browser display list based on current language settings."""
        return [
            get_string('COOKIES_BROWSER_DISPLAY_0', 'Disabled'),
            get_string('COOKIES_BROWSER_DISPLAY_1', 'Chrome'),
            get_string('COOKIES_BROWSER_DISPLAY_2', 'Edge'),
            get_string('COOKIES_BROWSER_DISPLAY_3', 'Firefox'),
            get_string('COOKIES_BROWSER_DISPLAY_4', 'Whale')
        ]

# Global singleton instance
STR = Strings()