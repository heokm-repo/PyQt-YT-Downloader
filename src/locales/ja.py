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

    'TITLE_INFO': "情報",
    'TITLE_WARNING': "警告",
    'TITLE_ERROR': "エラー",
    'TITLE_CONFIRM': "確認",

    # =========================================================================
    # 2. Main Window
    # =========================================================================
    'MAIN_URL_PLACEHOLDER': "YouTubeリンクを入力",
    'BTN_DOWNLOAD': "ダウンロード",
    'MAIN_EMPTY_STATE': "ダウンロードする動画がありません。\n上部にURLを入力して開始してください。",
    'MAIN_STATUS_READY': "準備完了",

    # =========================================================================
    # 3. Settings Dialog
    # =========================================================================
    'TITLE_SETTINGS': "設定",

    # Section: Save Location
    'TITLE_FOLDER_SELECT': "ダウンロードフォルダを選択",
    'SETTINGS_SEC_LOCATION': "保存場所",
    'SETTINGS_BTN_BROWSE': "参照",

    # Section: Quality & Format
    'SETTINGS_SEC_QUALITY': "品質とフォーマット",
    'SETTINGS_LABEL_VIDEO': "画質:",
    'SETTINGS_LABEL_AUDIO': "音質:",
    'SETTINGS_LABEL_FORMAT': "フォーマット:",
    'SETTINGS_HEADER_VIDEO': "=== ビデオ ===",
    'SETTINGS_HEADER_AUDIO': "=== オディオ ===",

    # Section: General Settings
    'SETTINGS_SEC_GENERAL': "一般設定",
    'SETTINGS_LABEL_MAX_DL': "最大ダウンロード数:",
    'SETTINGS_LABEL_LANGUAGE': "言語 (Language):",

    # Section: Advanced Features
    'SETTINGS_SEC_ADVANCED': "高度な機能",
    'SETTINGS_CHK_NORMALIZE': "音量正規化",
    'SETTINGS_CHK_ACCEL': "ダウンロード加速 (マルチスレッド)",
    'SETTINGS_LABEL_COOKIES': "Cookies Integration:",

    # Section: App Management
    'SETTINGS_SEC_APP_MANAGE': "アプリ管理",
    'SETTINGS_LABEL_VERSION': "現在のバージョン:",
    'SETTINGS_BTN_CHECK_UPDATE': "更新を確認",
    'SETTINGS_BTN_UNINSTALL': "アプリを削除",

    # Settings Errors
    'ERR_SETTINGS_NO_FOLDER': "ダウンロードフォルダを選択してください。",
    'ERR_SETTINGS_CREATE_FOLDER': "フォルダを作成できません:\n{error}",
    'ERR_SETTINGS_INVALID_FOLDER': "選択したパスは有効なフォルダではありません。",

    # =========================================================================
    # 4. Status Messages
    # =========================================================================
    'STATUS_WAITING': '待機中',
    'STATUS_WAITING_DOTS': '待機中...',
    'STATUS_DOWNLOADING': 'ダウンロード中',
    'STATUS_DOWNLOADING_DOTS': "ダウンロード中...",
    'STATUS_DOWNLOADING_SPEED': "ダウンロード中 ({speed})",
    
    'STATUS_PAUSED': '一時停止',
    'STATUS_PAUSED_SAVED': '一時停止 (保存済み)',
    'STATUS_IN_PROGRESS': '進行中',
    'STATUS_PREV_FAILED': '前のタスク失敗',
    
    'STATUS_CONVERTING': "変換中...",
    'STATUS_LOADING': "読み込み中...",
    'STATUS_COMPLETED': "完了",
    'STATUS_FAILED_FMT': "失敗: {message}",
    'STATUS_PREPARING': "準備中...",
    'STATUS_NO_IMAGE': "画像なし",

    # Worker Status
    'WORKER_MSG_CONVERTING': "変換/結合中",
    'WORKER_MSG_PROCESSING': "処理中...",
    'WORKER_MSG_COMPLETE': "ダウンロード完了",
    'WORKER_MSG_STOPPED': "ユーザーにより停止",

    # =========================================================================
    # 5. Dialogs & Popups
    # =========================================================================
    
    # URL Choice
    'TITLE_CHOICE': "ダウンロードオプション",
    'MSG_CHOICE_PLAYLIST': "動画とプレイリストの情報が含まれています。\n\nダウンロード方法を選択してください。",
    'BTN_CHOICE_ALL': "プレイリスト全体",
    'BTN_CHOICE_VIDEO': "動画のみ",

    # Duplicate / Resume
    'TITLE_DUPLICATE': "重複動画確認",
    'MSG_DUPLICATE_FOUND': "プレイリスト {total}個中 {duplicate}個は既にダウンロード済みです。\n重複を除外しますか？",
    'MSG_DUPLICATE_CHECK': "重複ダウンロード確認",
    'MSG_DUP_ALREADY_DONE': "既に '{format}' フォーマットでダウンロード済みです。\n",
    'MSG_DUP_IN_QUEUE': "(現在 {status} 状態のタスクがあります)\n",
    'MSG_DUP_ASK_OVERWRITE': "\n再度ダウンロード(上書き)しますか？",
    
    'TITLE_RESUME': "ダウンロード再開",
    'MSG_RESUME_CONFIRM': "以前のダウンロードタスクを再開しますか？",
    'TITLE_NO_NEW_VIDEOS': "通知",

    # Initialization & Update
    'TITLE_INIT': "YT Downloader 初期化",
    'TITLE_APP_UPDATE': "YT Downloader 更新",
    'MSG_INIT_TITLE': "初期化中...",
    'MSG_INIT_DESC': "必要なコンポーネントをダウンロードしています...",
    'MSG_INIT_PREPARING': "準備中...",
    'MSG_INIT_INFO': "お待ちください。これは初回のみ実行されます。",
    'MSG_INIT_DL_STATUS': "{item} をダウンロード中...",
    'MSG_INIT_COMPLETE': "初期化完了!",
    'MSG_INIT_STARTING': "起動中...",
    'MSG_INIT_FAILED': "初期化失敗",
    'ERR_INIT_DOWNLOAD': "ダウンロード中にエラーが発生しました。",
    'MSG_CONFIRM_INIT_DOWNLOAD': "動画のダウンロードと結合には必須コンポーネント(yt-dlp, FFmpeg)が必要です。\n\nダウンロードしますか？",
    'MSG_DOWNLOAD_COMPONENT_FAIL': "必須コンポーネントのダウンロードに失敗しました。",
    'MSG_CHECK_INTERNET': "インターネット接続を確認してください。",

    # Uninstall
    'TITLE_UNINSTALL': "削除確認",
    'MSG_UNINSTALL_CONFIRM': "本当に削除しますか？\n\n以下の項目が削除されます:\n• アプリデータ\n• 実行ファイル (exe)\n\nこの操作は取り消せません。",
    'TITLE_UNINSTALL_ERR': "削除エラー",
    'ERR_UNINSTALL_FAIL': "削除中にエラーが発生しました:\n{error}",
    'MSG_DEV_NO_UNINSTALL': "開発者モードではサポートされていません。",
    'ERR_UNINSTALL_START': "削除プロセスを開始できません。",

    # Update
    'TITLE_UPDATE_CHECK': "更新を確認",
    'MSG_UPDATE_AVAILABLE': "新しいバージョンが利用可能です!\n\n現在のバージョン: {current}\n最新バージョン: {latest}\n\n今すぐ更新しますか？",
    'MSG_UPDATE_LATEST': "最新バージョンを使用しています。",
    'ERR_UPDATE_CHECK': "更新の確認中にエラーが発生しました:\n{error}",
    'TITLE_UPDATE_DL': "更新中",
    'MSG_UPDATE_DL': "新しいバージョンをダウンロードしています...\nお待ちください。",
    'ERR_UPDATE_APPLY': "更新の適用に失敗しました。",
    'ERR_UPDATE_DOWNLOAD': "更新のダウンロードに失敗しました。",
    'MSG_UPDATE_COMPONENTS': "以下のコンポーネントの更新があります:\n\n",
    'MSG_UPDATE_ASK_NOW': "\n今すぐ更新しますか？",

    # =========================================================================
    # 6. Toast / Info Messages
    # =========================================================================
    'MSG_READY': "準備完了",
    'MSG_SMART_PASTE': "スマート貼り付け: ダウンロード開始",
    'MSG_DL_ENABLED': "ダウンロード有効化",
    'MSG_DL_PAUSED': "ダウンロード一時停止",
    'MSG_DL_CANCELLED': "キャンセルされました。",
    'MSG_ADDED_QUEUE': "キューに追加されました。",
    'MSG_ERROR_COUNT': "エラー: {count}",
    'MSG_COMPLETED_COUNT': "完了: {finished} / {total}",
    'MSG_NO_NEW_ITEMS': "新しい動画はありません。",
    'MSG_ALL_DONE': "完了",
    'ERR_PLAYLIST_FETCH': "プレイリストから動画を取得できませんでした。",
    'ERR_NOT_PLAYLIST': "プレイリストURLではありません。",
    'ERR_CANNOT_FETCH_INFO': "情報を取得できませんでした。",
    'ERR_INVALID_URL': "有効なYouTube URLを入力してください。",

    # Loading / Analysis
    'MSG_LOADING': "読み込み中...",
    'MSG_CHECKING_INFO': "情報確認中...",
    'MSG_FETCHING_INFO': "情報取得中...",
    'MSG_ANALYZING_PLAYLIST': "プレイリストを分析中...",
    'MSG_REGISTERING_PLAYLIST': "プレイリスト {count}個の動画を登録中...",
    'MSG_ADDED_PLAYLIST': "{count}個の動画が追加されました。",

    # System / Fatal Errors
    'ERR_MISSING_DEP': "必要なライブラリ '{module}' が見つかりません。",
    'MSG_INSTALL_DEP': "'pip install -r {file}' を実行してインストールしてください。",
    'TITLE_INIT_FAIL': "初期化失敗",
    'ERR_DL_COMPONENT_FAIL': "コンポーネントのダウンロードに失敗しました。",
    'MSG_CHECK_NET': "インターネット接続を確認してください。",
    'TITLE_INIT_ERR': "初期化エラー",
    'ERR_INIT_GENERIC': "初期化中にエラーが発生しました。",
    'ERR_MODULE_IMPORT': "モ듈をインポートできません。",
    'ERR_MODULE_HINT': "エラー: {error}\n\n必要なモ듈が不足している可能性があります。",
    'ERR_START_FAIL': "アプリケーションを開始できません。",
    'TITLE_FATAL': "致命的なエラー",
    'ERR_FATAL': "致命的なエラーが発生しました。",
    'ERR_YTDLP_MISSING': "yt-dlpが見つかりません",
    'ERR_YTDLP_RESTART': "yt-dlpが見つかりません。再起動してください。",
    'WARN_WORKER_TIMEOUT': "プレイリストワーカーが時間内に終了しませんでした。",

    # =========================================================================
    # 7. Tooltips & Context Menus
    # =========================================================================
    'TOOLTIP_PAUSE': "一時停止",
    'TOOLTIP_CANCEL': "キャンセルして削除",
    'TOOLTIP_RESUME': "再開",
    'TOOLTIP_REMOVE': "リストから削除",
    'TOOLTIP_PLAY': "再生",
    'TOOLTIP_OPEN_FOLDER': "フォルダを開く",
    'TOOLTIP_DELETE_FILE': "ファイルを削除",
    'TOOLTIP_RETRY': "再試行",
    'TOOLTIP_NORMALIZE': "音量を放送基準(-14 LUFS)に正規化します。\n変換に時間がかかります。",
    'TOOLTIP_ACCEL': "ファイルを分割して並行ダウンロードします。\n速度が向上します。\n(選択時は最大ダウンロード数が1に固定されます)",

    'MENU_PLAY': "▶ 再生",
    'MENU_OPEN_FOLDER': "📂 フォルダを開く",
    'MENU_COPY_URL': "🔗 URLをコピー",
    'MENU_PAUSE': "⏸ 一時停止",
    'MENU_RESUME': "▶ 再開",
    'MENU_RETRY': "↻ 再試行",
    'MENU_DELETE_FILE': "🗑️ ファイルを削除",
    'MENU_REMOVE': "❌ リストから削除",

    # =========================================================================
    # 8. Task Actions & Confirmations
    # =========================================================================
    'ERR_TASK_NOT_FOUND': "タスクが見つかりません。",
    'ERR_NO_FILE_PATH': "ファイルパスが保存されていません。",
    'ERR_EXECUTE_FILE': "ファイルを実行できません:\n{error}",
    'ERR_FILE_NOT_FOUND_PATH': "ファイルが見つかりません。\n\nパス: {path}",
    'ERR_OPEN_FOLDER': "フォルダを開けません: {error}",
    
    'TITLE_DELETE_CONFIRM': "削除確認",
    'MSG_DELETE_CONFIRM': "本当に削除しますか？\nこの操作は取り消せません。",
    'MSG_DELETE_CONFIRM_MANY': "本当に {count}個のファイルを削除しますか？\nこの操作は取り消せません。",
    
    'TITLE_DELETE_FAILED': "削除失敗",
    'ERR_DELETE_PERMISSION': "ファイルが使用中か権限がありません:\n{path}",
    'ERR_DELETE_ERROR': "ファイルを削除できません:\n{error}",
    
    'TITLE_REMOVE_CONFIRM': "削除確認",
    'MSG_REMOVE_CONFIRM': "{count}個の項目をリストから削除しますか？",

    # =========================================================================
    # 9. Constants & Lists
    # =========================================================================
    'TPL_VIDEO_TITLE': "動画ID: {video_id}",

    'COOKIES_BROWSER_DISPLAY_0': "無効",
    'COOKIES_BROWSER_DISPLAY_1': "Chrome",
    'COOKIES_BROWSER_DISPLAY_2': "Edge",
    'COOKIES_BROWSER_DISPLAY_3': "Firefox",
    'COOKIES_BROWSER_DISPLAY_4': "Whale",
}
