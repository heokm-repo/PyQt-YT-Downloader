"""yt-dlp option builder helpers."""

import os

from constants import (
    AUDIO_FORMATS,
    CONCURRENT_FRAGMENT_DOWNLOADS,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_FORMAT,
    KEY_UNIVERSAL_COMPATIBILITY,
    OUTPUT_TEMPLATE,
)
from core.download.quality_policy import (
    build_audio_quality_profile,
    build_video_source_selector,
)
from core.download.audio_source_policy import build_audio_source_policy
from utils.logger import log
from utils.utils import is_youtube_url
from core.download.temp_workspace import task_temp_path
from core.download.workspace_identity import is_workspace_id
from core.download.workspace_migration import prepare_task_workspace


REMUX_VIDEO_FORMATS = frozenset(('mp4', 'mkv'))


def _build_base_options(
    save_path,
    ffmpeg_path,
    is_playlist,
    settings=None,
    is_resume=False,
    url=None,
    temp_identity=None,
):
    """
    Build base yt-dlp options.
    
    Args:
        save_path: Output directory.
        ffmpeg_path: Optional FFmpeg executable path.
        is_playlist: Whether the task is a playlist.
        settings: Optional settings dictionary.
        is_resume: Whether the task is resuming.
    
    Returns:
        Base options dictionary.
    """
    # Read the output template from settings, or use the default.
    # Important: outtmpl must stay relative so --paths home: and --paths temp: work together.
    output_template = settings.get('output_template', OUTPUT_TEMPLATE) if settings else OUTPUT_TEMPLATE
    
    opts = {
        'outtmpl': output_template,
        'noplaylist': not is_playlist,
    }
    
    # Isolate concurrent downloads while keeping resume paths deterministic.
    identity = temp_identity or {}
    workspace_id = identity.get("workspace_id")
    if is_workspace_id(workspace_id):
        preparation = prepare_task_workspace(
            save_path,
            str(workspace_id),
            migrate_legacy=(
                is_resume and identity.get("legacy_workspace") is True
            ),
            legacy_identity=identity.get("legacy_identity"),
        )
        temp_path = preparation.workspace_path
    else:
        # Keep direct option-builder callers compatible with pre-UUID tasks.
        temp_path = task_temp_path(
            save_path,
            identity.get("extractor", "unknown"),
            identity.get("id") or url,
            (settings or {}).get("format", DEFAULT_FORMAT),
        )
    os.makedirs(temp_path, exist_ok=True)
    opts['temp_path'] = temp_path
    opts['home_path'] = temp_path
    
    # Allow overwrites only when this is not a resume operation.
    # Keep .part files when resuming.
    if not is_resume:
        opts['overwrites'] = True
    
    if ffmpeg_path:
        opts['ffmpeg_location'] = ffmpeg_path
    else:
        log.warning("FFmpeg not found")
    
    return opts


def _build_format_options(settings):
    """
    Build yt-dlp format options from the selected container, video quality,
    and audio quality settings.
    """
    opts = {}
    fmt = str(settings.get('format', DEFAULT_FORMAT)).strip().lower()
    if settings.get(KEY_UNIVERSAL_COMPATIBILITY) and fmt not in {"mp4", "mp3"}:
        fmt = "mp4"
    normalize_audio = bool(settings.get('normalize_audio'))
    requested_audio_quality = (
        DEFAULT_AUDIO_QUALITY
        if fmt == 'wav'
        else settings.get('audio_quality', DEFAULT_AUDIO_QUALITY)
    )
    audio_profile = build_audio_quality_profile(requested_audio_quality)
    audio_policy = build_audio_source_policy(fmt, requested_audio_quality)

    if fmt in AUDIO_FORMATS:
        if fmt in {"mp3", "wav"}:
            opts['format'] = audio_profile.source_format
        else:
            opts['format'] = audio_policy.audio_only_selector
    else:
        source_selector, format_sort = build_video_source_selector(
            settings.get('video_quality'),
            audio_policy,
        )
        opts['format'] = source_selector
        if format_sort:
            # yt-dlp defines "res" as the smaller video dimension, so the
            # quality cap works consistently for landscape and portrait video.
            opts['format_sort'] = format_sort

        if fmt == 'webm':
            # The app owns the exact-path WebM pass. This lets it copy compatible
            # streams and encode only the incompatible streams or requested audio.
            return opts

        opts['merge_output_format'] = fmt
        if fmt in REMUX_VIDEO_FORMATS:
            opts['remux_video'] = fmt

    return opts


def _build_advanced_options(settings, url: str | None = None):
    """
    Build advanced options for acceleration, cookies, and JavaScript runtime settings.
    
    Args:
        settings: Settings dictionary.
        url: URL whose hostname determines whether YouTube cookies are used.
    
    Returns:
        Advanced options dictionary.
    """
    opts = {}
    
    # Acceleration using concurrent fragments.
    if settings.get('use_acceleration'):
        concurrent_downloads = settings.get('concurrent_fragment_downloads', CONCURRENT_FRAGMENT_DOWNLOADS)
        opts['concurrent_fragment_downloads'] = concurrent_downloads
    
    # Use cookies from the in-app login flow.
    try:
        from utils.cookie_store import get_cookie_file_path, cookie_file_exists
        if is_youtube_url(url) and cookie_file_exists():
            cookie_path = get_cookie_file_path()
            opts['cookiefile'] = cookie_path
            log.info(f"Using cookie file: {cookie_path}")
    except ImportError:
        log.debug("cookie_store module not available, skipping cookie support")
    
    # QuickJS runtime path needed by yt-dlp signature extraction.
    try:
        from utils.bin.manager import get_quickjs_path
        qjs_path = get_quickjs_path()
        if qjs_path:
            opts['js_runtimes'] = f"quickjs:{qjs_path}"
            log.info(f"Using QuickJS runtime: {qjs_path}")
    except ImportError:
        log.debug("bin_manager module not available, skipping QuickJS runtime support")
    
    return opts


def _add_runtime_extract_options(
    opts: dict,
    settings: dict | None = None,
    url: str | None = None,
    temp_identity: dict | None = None,
) -> dict:
    advanced_opts = _build_advanced_options(settings or {}, url)
    for key in ("cookiefile", "js_runtimes"):
        if key in advanced_opts:
            opts[key] = advanced_opts[key]
    return opts


def _build_playlist_extract_options(
    settings: dict | None = None,
    url: str | None = None,
) -> dict:
    opts = {"extract_flat": True}
    return _add_runtime_extract_options(opts, settings, url)


def _build_metadata_extract_options(
    settings: dict | None = None,
    is_playlist: bool = False,
    url: str | None = None,
) -> dict:
    opts = {
        "extract_flat": "in_playlist",
        "noplaylist": not is_playlist,
    }

    if settings:
        opts.update(_build_format_options(settings))

    return _add_runtime_extract_options(opts, settings, url)

def _build_all_options(
    settings,
    save_path,
    ffmpeg_path,
    is_playlist,
    is_resume=False,
    url: str | None = None,
    temp_identity: dict | None = None,
) -> dict:
    """Assemble the final yt-dlp options dictionary."""
    # Merge base options.
    ydl_opts = {}
    ydl_opts.update(
        _build_base_options(
            save_path,
            ffmpeg_path,
            is_playlist,
            settings,
            is_resume,
            url,
            temp_identity,
        )
    )
    ydl_opts.update(_build_format_options(settings))
    ydl_opts.update(_build_advanced_options(settings, url))
    
    return ydl_opts

# =====================================================================
# Generic download execution.
