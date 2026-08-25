"""
日本語文字列定義 (Japanese)
"""
STRINGS = {
    # =========================================================================
    # 1. Common / Global
    # =========================================================================
    'BTN_OK': "OK",
    'BTN_YES': "はい",
    'BTN_NO': "いいえ",
    'BTN_CLOSE': "閉じる",
    'BTN_CANCEL': "キャンセル",
    'BTN_SAVE': "保存",
    'BTN_RESTART_NOW': "今すぐ再起動",
    'BTN_LATER': "後で",

    'TITLE_WARNING': "警告",
    'TITLE_ERROR': "エラー",

    # =========================================================================
    # 2. Main Window
    # =========================================================================
    'MAIN_URL_PLACEHOLDER': "動画URLを入力",
    'BTN_DOWNLOAD': "ダウンロード",
    'MAIN_EMPTY_STATE': "ダウンロードする動画がありません。\n上部にURLを入力して開始してください。",
    'MAIN_STATUS_READY': "準備完了",

    # =========================================================================
    # 3. Settings Dialog
    # =========================================================================
    'TITLE_SETTINGS': "設定",

    # Section: Save Location
    'TITLE_FOLDER_SELECT': "フォルダーの選択",
    'TITLE_LICENSE': "ライセンス情報",
    'SETTINGS_SEC_LOCATION': "保存場所",
    'SETTINGS_BTN_BROWSE': "参照",

    # Section: Quality & Format
    'SETTINGS_SEC_QUALITY': "品質とフォーマット",
    'SETTINGS_LABEL_VIDEO': "画質:",
    'SETTINGS_LABEL_AUDIO': "音質:",
    'SETTINGS_LABEL_FORMAT': "フォーマット:",
    'SETTINGS_HEADER_VIDEO': "=== ビデオ ===",
    'SETTINGS_HEADER_AUDIO': "=== オーディオ ===",

    # Section: General Settings
    'SETTINGS_SEC_GENERAL': "一般設定",
    'SETTINGS_LABEL_MAX_DL': "最大同時ダウンロード数:",
    'SETTINGS_LABEL_LANGUAGE': "言語 (Language):",
    'SETTINGS_LABEL_THEME': "テーマ:",
    'SETTINGS_THEME_LIGHT': "ライト",
    'SETTINGS_THEME_DARK': "ダーク",

    # Section: Advanced Features
    'SETTINGS_SEC_ADVANCED': "高度な機能",
    'SETTINGS_CHK_NORMALIZE': "音量正規化",
    'SETTINGS_CHK_ACCEL': "ダウンロード加速 (マルチスレッド)",
    'SETTINGS_CHK_COMPATIBILITY': "高互換性モード",
    'SETTINGS_LABEL_COOKIES': "アプリ内ログイン:",
    'BTN_LOGIN': "ログイン",
    'BTN_SAVE_CLOSE': "保存して閉じる",
    'TITLE_LOGIN_BROWSER': "YouTubeログイン",
    'MSG_LOGIN_WAITING': "Googleアカウントでログインしてください。",
    'MSG_LOGIN_SUCCESS': "ログイン検出！「保存して閉じる」をクリックしてください。",
    'MSG_LOGIN_STABILIZING': "ログインを完了しています...",
    'ERR_LOGIN_NO_COOKIES': "YouTube Cookieを取得できませんでした！",
    'ERR_LOGIN_SAVE_FAILED': "保存に失敗しました: {error}",

    'BTN_LOGOUT': "ログアウト",
    'TITLE_LOGOUT': "ログアウト",
    'MSG_LOGOUT_CONFIRM': "保存したYouTube Cookieとブラウザーのログインデータを削除しますか？",
    'MSG_LOGOUT_SUCCESS': "保存したCookieとブラウザーのログインデータを削除しました。",
    'ERR_LOGOUT_FAILED': "一部のログインデータを削除できませんでした。ログイン画面を閉じて、もう一度お試しください。",

    # Section: App Management
    'SETTINGS_SEC_APP_MANAGE': "アプリ管理",
    'SETTINGS_LABEL_VERSION': "現在のバージョン:",
    'SETTINGS_BTN_CHECK_UPDATE': "更新を確認",
    'SETTINGS_BTN_UNINSTALL': "アプリをアンインストール",
    'SETTINGS_BTN_LICENSE': "ライセンス情報",
    'SETTINGS_BTN_SPONSOR': "支援する",

    # Settings Errors
    'ERR_SETTINGS_NO_FOLDER': "ダウンロードフォルダーを選択してください。",
    'ERR_SPONSOR_OPEN': "スポンサーページを開けませんでした。",
    'MSG_DOWNLOAD_FOLDER_FALLBACK': "ダウンロードフォルダーを使用できないため、保存先を変更しました。\n\n以前の保存先:\n{old_path}\n\n新しい保存先:\n{new_path}\n\n理由:\n{reason}",

    # =========================================================================
    # 4. Status Messages
    # =========================================================================

    'STATUS_WAITING_DOTS': '待機中...',

    'STATUS_DOWNLOADING_DOTS': "ダウンロード中...",
    'STATUS_DOWNLOADING_SPEED': "ダウンロード中 ({speed})",
    
    'STATUS_PAUSED': '一時停止',
    'STATUS_PAUSED_SAVED': '一時停止 (保存済み)',
    'STATUS_PAUSED_CANCELLED': 'キャンセル済み (一時ファイル削除済み)',
    'STATUS_IN_PROGRESS': '進行中',

    
    'STATUS_CONVERTING': "変換中...",

    'STATUS_COMPLETED': "完了",
    'STATUS_FAILED_FMT': "失敗: {message}",
    'STATUS_PREPARING': "準備中...",
    'STATUS_NO_IMAGE': "画像なし",

    # =========================================================================
    # 5. Dialogs & Popups
    # =========================================================================
    
    # URL Choice
    'TITLE_CHOICE': "ダウンロードオプション",
    'MSG_CHOICE_PLAYLIST': "動画とプレイリストの情報が含まれています。\n\nダウンロードする内容を選択してください。",
    'BTN_CHOICE_ALL': "プレイリスト全体",
    'BTN_CHOICE_VIDEO': "この動画のみ",

    # Duplicate / Resume
    'TITLE_DUPLICATE': "重複動画確認",
    'MSG_DUPLICATE_FOUND': "ダウンロード済み：{duplicate} / {total}\n重複動画を除外しますか？",
    'MSG_DUPLICATE_CHECK': "重複ダウンロード確認",
    'MSG_DUP_ALREADY_DONE': "既に「{format}」形式でダウンロード済みです。\n",
    'MSG_DUP_IN_QUEUE': "（タスクは現在「{status}」状態です）\n",
    'MSG_DUP_ASK_OVERWRITE': "\n再度ダウンロードして上書きしますか？",
    'ERR_DUPLICATE_REPLACEMENT_TIMEOUT': "既存のダウンロードが時間内に停止しなかったため、新しいダウンロードは開始されませんでした。",
    
    'TITLE_RESUME': "ダウンロード再開",
    'MSG_RESUME_CONFIRM': "以前に一時停止したダウンロードを再開しますか？",
    'TITLE_NO_NEW_VIDEOS': "通知",

    # Initialization & Update
    'MSG_INIT_DESC': "必要なコンポーネントをダウンロードしています...",
    'MSG_INIT_PREPARING': "準備中...",
    'MSG_INIT_INFO': "お待ちください。これは初回のみ実行されます。",
    'MSG_INIT_DL_STATUS': "{item} をダウンロード中...",
    'MSG_INIT_COMPLETE': "初期化完了！",
    'MSG_INIT_STARTING': "起動中...",
    'MSG_INIT_FAILED': "初期化失敗",
    'ERR_INIT_DOWNLOAD': "ダウンロード中にエラーが発生しました。",
    'MSG_INIT_CANCELLING': "キャンセル中...",
    'MSG_INIT_DOWNLOAD_CANCELLED': "ダウンロードをキャンセルしました。",




    # Init & Update
    'TITLE_INIT': "YT Downloader 初期化",
    'TITLE_INIT_SETUP': "初期設定",
    'LABEL_LANGUAGE_SELECT': "言語選択:",
    'MSG_CONFIRM_INIT_DOWNLOAD': "動画のダウンロード、ファイルの結合、メディアの検査、YouTubeコンテンツの処理には必須コンポーネント（yt-dlp、FFmpeg、ffprobe、QuickJS）が必要です。\n\nダウンロードしますか？",
    'BTN_START_SETUP': "開始",

    'TITLE_APP_UPDATE': "YT Downloader 更新",

    # Startup Dialog
    'TITLE_STARTUP': "YT Downloader 起動中",
    'MSG_STARTUP_CHECK_EXT': "外部コンポーネントを確認中...",
    'MSG_STARTUP_CHECK_APP': "アプリのアップデートを確認中...",
    'MSG_STARTUP_OPENING': "アプリを開いています...",

    # Uninstall
    'TITLE_UNINSTALL': "アンインストールの確認",
    'MSG_UNINSTALL_CONFIRM': "YT Downloaderをアンインストールしますか？\n\n以下の項目が削除されます:\n• アプリデータ\n• 実行ファイル (exe)\n\nこの操作は取り消せません。",
    'TITLE_UNINSTALL_ERR': "アンインストールエラー",
    'ERR_UNINSTALL_FAIL': "アンインストール中にエラーが発生しました:\n{error}",
    'MSG_DEV_NO_UNINSTALL': "開発者モードではアプリのアンインストールはサポートされていません。",
    'ERR_UNINSTALL_START': "アンインストール処理を開始できません。",

    # Update
    'TITLE_UPDATE_CHECK': "更新を確認",
    'MSG_UPDATE_AVAILABLE': "新しいバージョンが利用可能です！\n\n現在のバージョン: {current}\n最新バージョン: {latest}\n\n今すぐ更新しますか？",
    'MSG_UPDATE_LATEST': "最新バージョンを使用しています。",
    'MSG_UPDATE_ALL_LATEST': "YT Downloaderとすべての必須コンポーネントは最新です。",
    'MSG_UPDATE_COMPONENT_MISSING': "• {name}: インストールまたは修復が必要",
    'MSG_UPDATE_RESTART_REQUIRED': "更新を適用するには、アプリを再起動してください。",
    'MSG_UPDATE_RESTART_ACTIVE_TASKS': "実行中のダウンロードとキュー内のタスクは再起動時に一時停止され、アプリの再起動後に再開できます。",
    'ERR_RESTART_FAILED': "アプリを再起動できませんでした。手動で再起動してください。",
    'ERR_UPDATE_CHECK': "更新の確認中にエラーが発生しました:\n{error}",
    'MSG_UPDATE_DL': "新しいバージョンをダウンロードしています...\nお待ちください。",
    'MSG_UPDATE_PREPARING': "更新を準備しています...",
    'MSG_UPDATE_DL_STATUS': "更新をダウンロードしています...",
    'MSG_UPDATE_INSTALLING': "更新のダウンロードが完了しました。インストーラーを起動します...",
    'MSG_UPDATE_CANCELLED': "更新がキャンセルされました。",
    'ERR_UPDATE_APPLY': "更新の適用に失敗しました。",
    'ERR_UPDATE_DOWNLOAD': "更新のダウンロードに失敗しました。",
    'MSG_UPDATE_COMPONENTS': "以下のコンポーネントの更新があります:\n\n",
    'MSG_UPDATE_ASK_NOW': "\n今すぐ更新しますか？",

    # Worker Status
    'WORKER_MSG_CONVERTING': "変換/結合中",
    'WORKER_MSG_PROCESSING': "処理中...",
    'WORKER_MSG_COMPLETED': "ダウンロード完了",
    'WORKER_MSG_STOPPED': "ユーザーにより停止されました",

    # =========================================================================
    # 6. Toast / Info Messages
    # =========================================================================
    'MSG_READY': "準備完了",
    'MSG_SMART_PASTE': "スマートペースト：ダウンロードを開始しました。",
    'MSG_LICENSE_INFO': "Font Awesome提供のアイコン (SIL OFL 1.1)\nMaterial Design Icons (Apache 2.0)\n\nサードパーティ製ソフトウェア:\n- yt-dlp (The Unlicense)\n- FFmpeg (GPL / LGPL)\n- QuickJS (MIT)\n\nこのソフトウェアは GNU General Public License v3.0 に基づいて配布されています。",
    'MSG_DL_ENABLED': "ダウンロード有効化",
    'MSG_DL_PAUSED': "ダウンロード一時停止",
    'MSG_DL_CANCELLED': "キャンセルされました。",
    'MSG_ADDED_QUEUE': "キューに追加されました。",
    'MSG_ERROR_COUNT': "エラー: {count}",
    'MSG_COMPLETED_COUNT': "完了: {finished} / {total}",
    'SORT_NEWEST': "新しい順",
    'SORT_OLDEST': "古い順",
    'SORT_STATUS': "状態順",
    'MSG_NO_NEW_ITEMS': "新しい動画はありません。",
    'MSG_PLAYLIST_EMPTY': "このプレイリストには動画がありません。",
    'MSG_PLAYLIST_NO_AVAILABLE_VIDEOS': "このプレイリストから取得できる動画はありません。",
    'ERR_PLAYLIST_FETCH': "プレイリストから動画を取得できませんでした。",
    'ERR_NOT_PLAYLIST': "プレイリストURLではありません。",
    'ERR_CANNOT_FETCH_INFO': "情報を取得できませんでした。",
    'ERR_INVALID_URL': "有効な動画URLを入力してください。",
    'ERR_UNSUPPORTED_URL': "このURLからのダウンロードには対応していません。",

    # Loading / Analysis
    'MSG_LOADING': "読み込み中...",
    'MSG_CHECKING_INFO': "情報確認中...",
    'MSG_FETCHING_INFO': "情報取得中...",
    'MSG_ANALYZING_PLAYLIST': "プレイリストを分析中...",
    'MSG_REGISTERING_PLAYLIST': "プレイリスト内の動画をキューに追加中... ({count})",
    'MSG_ADDED_PLAYLIST': "キューに追加したプレイリスト動画：{count}本",

    # System / Fatal Errors
    'ERR_MISSING_DEP': "必要なライブラリ '{module}' が見つかりません。",
    'MSG_INSTALL_DEP': "「pip install -r {file}」を実行して、必要なライブラリをインストールしてください。",
    'TITLE_INIT_FAIL': "初期化失敗",
    'ERR_DL_COMPONENT_FAIL': "コンポーネントのダウンロードに失敗しました。",
    'MSG_CHECK_NET': "インターネット接続を確認して、もう一度お試しください。",

    'ERR_INIT_GENERIC': "初期化中にエラーが発生しました。",
    'ERR_MODULE_IMPORT': "モジュールをインポートできません。",
    'ERR_MODULE_HINT': "エラー: {error}\n\n必要なモジュールが不足している可能性があります。",
    'ERR_START_FAIL': "アプリケーションを起動できません。",
    'TITLE_FATAL': "致命的なエラー",
    'ERR_FATAL': "致命的なエラーが発生しました。",
    'ERR_YTDLP_MISSING': "yt-dlpが見つかりません",
    'ERR_YTDLP_RESTART': "yt-dlpが見つかりません。再起動してください。",


    # =========================================================================
    # 7. Tooltips & Context Menus
    # =========================================================================
    'TOOLTIP_PAUSE': "一時停止",
    'TOOLTIP_CANCEL': "キャンセルして削除",
    'TOOLTIP_RESUME': "再開",
    'TOOLTIP_REMOVE': "リストから削除",
    'TOOLTIP_PLAY': "再生",
    'TOOLTIP_OPEN_FOLDER': "フォルダーを開く",
    'TOOLTIP_DELETE_FILE': "ファイルを削除",
    'TOOLTIP_RETRY': "再試行",
    'TOOLTIP_NORMALIZE': "音量を-14 LUFSに正規化します。\n変換に時間がかかります。",
    'TOOLTIP_ACCEL': "ファイルを分割して並行ダウンロードします。\n速度が向上する場合があります。\n（有効にすると最大同時ダウンロード数が1に固定されます）",
    'TOOLTIP_COMPATIBILITY': "出力形式をMP4またはMP3に制限します。\nMP4動画をH.264/AACでエンコードして、幅広い機器との互換性を確保します。",

    'MENU_PLAY': "再生",
    'MENU_OPEN_FOLDER': "フォルダーを開く",
    'MENU_COPY_URL': "URLをコピー",
    'MENU_PAUSE': "一時停止",
    'MENU_RESUME': "再開",
    'MENU_RETRY': "再試行",
    'MENU_DELETE_FILE': "ファイルを削除",
    'MENU_REMOVE': "リストから削除",
    'MENU_REMOVE_COMPLETED': "完了した項目のみリストから削除",

    # =========================================================================
    # 8. Task Actions & Confirmations
    # =========================================================================
    'ERR_TASK_NOT_FOUND': "タスクが見つかりません。",
    'ERR_NO_FILE_PATH': "ファイルパスが保存されていません。",
    'ERR_EXECUTE_FILE': "ファイルを実行できません:\n{error}",
    'ERR_FILE_NOT_FOUND_PATH': "ファイルが見つかりません。\n\nパス: {path}",
    'ERR_OPEN_FOLDER': "フォルダーを開けません: {error}",
    
    'TITLE_DELETE_CONFIRM': "削除確認",
    'MSG_DELETE_CONFIRM': "本当に削除しますか？\nこの操作は取り消せません。",
    'MSG_DELETE_CONFIRM_MANY': "本当に {count}個のファイルを削除しますか？\nこの操作は取り消せません。",
    
    'TITLE_DELETE_FAILED': "削除失敗",
    'ERR_DELETE_PERMISSION': "ファイルが使用中か権限がありません:\n{path}",
    'ERR_DELETE_ERROR': "ファイルを削除できません:\n{error}",
    
    'TITLE_REMOVE_CONFIRM': "リストからの削除確認",
    'MSG_REMOVE_CONFIRM': "選択した項目をリストから削除しますか？（{count}）",
    'MSG_REMOVE_COMPLETED_CONFIRM': "完了した項目をリストから削除しますか？（{count}）",

    # =========================================================================
    # 9. Constants & Lists
    # =========================================================================
    'TPL_VIDEO_TITLE': "動画ID: {video_id}",

    # COOKIES_BROWSER_DISPLAY removed (replaced by in-app login)
}
