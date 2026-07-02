"""Download execution helpers backed by yt-dlp."""

from constants import ERROR_INVALID_URL, MSG_DOWNLOAD_COMPLETE, MSG_PAUSED_BY_USER
from core.download.options import _build_all_options
from core.youtube_url import _sanitize_url
from core.ytdlp.wrapper import YtDlpWrapper
from locales.strings import STR
from utils.bin.manager import get_ytdlp_path
from utils.logger import log
from utils.settings_store import get_download_folder
from utils.utils import get_ffmpeg_path, is_youtube_url


def download_video(url, settings, progress_hook, is_resume=False, stop_check=None):
    """Download a single URL through yt-dlp."""
    if not url:
        return False, ERROR_INVALID_URL

    if is_youtube_url(url):
        clean_url, is_playlist = _sanitize_url(url)
    else:
        clean_url = url
        is_playlist = False

    ytdlp_path = get_ytdlp_path()
    if not ytdlp_path:
        return False, STR.ERR_YTDLP_RESTART

    save_path = get_download_folder(settings)
    ffmpeg_path = get_ffmpeg_path()
    ydl_opts = _build_all_options(settings, save_path, ffmpeg_path, is_playlist, progress_hook, is_resume)

    try:
        wrapper = YtDlpWrapper(ytdlp_path, ffmpeg_path)
        success, message = wrapper.download(clean_url, ydl_opts, progress_hook, is_resume, stop_check)

        if success:
            return True, MSG_DOWNLOAD_COMPLETE

        if MSG_PAUSED_BY_USER in message:
            return False, MSG_PAUSED_BY_USER
        return False, message
    except Exception as exc:
        error_msg = str(exc)
        if MSG_PAUSED_BY_USER in error_msg:
            return False, MSG_PAUSED_BY_USER

        log.error(f"Download Error: {error_msg}", exc_info=True)
        return False, error_msg
