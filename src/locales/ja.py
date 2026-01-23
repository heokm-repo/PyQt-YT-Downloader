"""
日本語文字列定義
"""
STRINGS = {
    # 設定ダイアログ
    'SETTINGS_DIALOG_TITLE': "設定",
    'SETTINGS_CLOSE_BUTTON_TEXT': "✕",
    'SETTINGS_SECTION_SAVE_LOCATION': "保存場所",
    'SETTINGS_BROWSE_BUTTON_TEXT': "参照",
    'SETTINGS_SECTION_QUALITY_FORMAT': "品質とフォーマット",
    'SETTINGS_LABEL_VIDEO_QUALITY': "画質:",
    'SETTINGS_LABEL_AUDIO_QUALITY': "音質:",
    'SETTINGS_LABEL_FORMAT': "フォーマット:",
    'SETTINGS_SECTION_GENERAL': "一般設定",
    'SETTINGS_LABEL_MAX_DOWNLOADS': "最大ダウンロード数:",
    'SETTINGS_SECTION_ADVANCED': "高度な機能",
    'SETTINGS_CHECKBOX_NORMALIZE': "音量正規化 (Loudness Normalization)",
    'SETTINGS_CHECKBOX_ACCELERATION': "ダウンロード加速 (マルチスレッド)",
    'SETTINGS_BUTTON_CANCEL': "キャンセル",
    'SETTINGS_BUTTON_SAVE': "保存",
    'SETTINGS_FOLDER_DIALOG_TITLE': "ダウンロードフォルダを選択",
    'SETTINGS_ERROR_TITLE': "エラー",
    'SETTINGS_ERROR_NO_FOLDER': "ダウンロードフォルダを選択してください。",
    'SETTINGS_ERROR_CANNOT_CREATE_FOLDER': "フォルダを作成できません:\n{error}",
    'SETTINGS_ERROR_INVALID_FOLDER': "選択したパスは有効なフォルダではありません。",
    
    # メインウィンドウ
    'APP_TITLE': "YT Downloader",
    'TITLE_BAR_MINIMIZE_BUTTON_TEXT': "─",
    'TITLE_BAR_CLOSE_BUTTON_TEXT': "✕",
    'URL_INPUT_PLACEHOLDER': "YouTubeリンクを入力",
    'DOWNLOAD_BUTTON_TEXT': "ダウンロード",
    'SETTINGS_BUTTON_TEXT': "⚙",
    'EMPTY_STATE_MESSAGE': "ダウンロードする動画がありません。\n上部にURLを入力して開始してください。",
    'STATUS_BAR_DEFAULT_TEXT': "準備完了",
    
    # タスク状態
    'STATUS_TEXT_WAITING': '待機中',
    'STATUS_TEXT_DOWNLOADING': 'ダウンロード中',
    'STATUS_TEXT_PAUSED': '一時停止',
    'STATUS_TEXT_IN_PROGRESS': '進行中',
    'STATUS_TEXT_WAITING_DOTS': '待機中...',
    'STATUS_TEXT_PAUSED_SAVED': '一時停止 (保存済み)',
    'STATUS_TEXT_PREVIOUS_FAILED': '前のタスク失敗',
    
    # メッセージ
    'MSG_READY': "準備完了",
    'MSG_SMART_PASTE_STARTED': "スマート貼り付け: ダウンロード開始",
    'MSG_DOWNLOAD_ENABLED': "ダウンロード有効化",
    'MSG_DOWNLOAD_PAUSED': "ダウンロード一時停止",
    'MSG_DOWNLOAD_CANCELLED': "ダウンロードがキャンセルされました。",
    'MSG_ADDED_TO_QUEUE': "キューに追加されました。",
    'MSG_PLAYLIST_ANALYZING': "プレイリストを分析中...",
    'MSG_PLAYLIST_REGISTERING': "プレイリスト {count}個の動画を登録中...",
    'MSG_PLAYLIST_ADDED': "プレイリスト {count}個の動画がキューに追加されました。",
    'MSG_ERROR_COUNT': "エラー: {count}個",
    'MSG_COMPLETED_COUNT': "完了: {finished} / {total}",
    'MSG_NO_NEW_VIDEOS': "追加する新しい動画がありません。",
    'MSG_PLAYLIST_FETCH_ERROR': "プレイリストから動画を取得できませんでした。",
    'MSG_DOWNLOAD_COMPLETE': "完了",
    'MSG_NOT_PLAYLIST_URL': "プレイリストURLではありません。",
    'MSG_CANNOT_FETCH_INFO': "情報を取得できませんでした。",
    
    # ダイアログ
    'DIALOG_DUPLICATE_VIDEOS_TITLE': "重複動画確認",
    'DIALOG_DUPLICATE_VIDEOS_MESSAGE': "プレイリスト {total}個中 {duplicate}個は既にダウンロードした動画です。\n重複した動画を除外しますか？",
    'DIALOG_RESUME_DOWNLOAD_TITLE': "ダウンロード再開",
    'DIALOG_RESUME_DOWNLOAD_MESSAGE': "以前にダウンロード中のタスクを再開しますか？",
    'DIALOG_NO_NEW_VIDEOS_TITLE': "通知",
    
    # 重複ダウンロード
    'DUPLICATE_CHECK_TITLE': "重複ダウンロード確認",
    'DUPLICATE_MSG_ALREADY_DOWNLOADED': "既に '{format}' フォーマットでダウンロードされた動画です。\n",
    'DUPLICATE_MSG_IN_QUEUE': "(現在 {status} 状態のタスクがあります)\n",
    'DUPLICATE_MSG_ASK_OVERWRITE': "\n再度ダウンロード(上書き)しますか？",
    
    # プレイリスト
    'PLAYLIST_VIDEO_TITLE_TEMPLATE': "動画ID: {video_id}",
    
    # 警告
    'WARNING_PLAYLIST_WORKER_TIMEOUT': "プレイリストワーカーが時間内に終了しませんでした。",
}
