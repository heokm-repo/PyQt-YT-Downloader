"""yt-dlp option builder helpers."""

import os
import re
from dataclasses import dataclass

from constants import (
    AUDIO_CHANNELS,
    AUDIO_FORMATS,
    CONCURRENT_FRAGMENT_DOWNLOADS,
    DEFAULT_AUDIO_QUALITY,
    DEFAULT_FORMAT,
    DEFAULT_VIDEO_QUALITY,
    FORMAT_BESTAUDIO,
    LOUDNORM_FILTER,
    OUTPUT_TEMPLATE,
    YTDL_TEMP_DIR,
)
from utils.logger import log


def _build_base_options(save_path, ffmpeg_path, is_playlist, progress_hook, settings=None, is_resume=False):
    """
    Build base yt-dlp options.
    
    Args:
        save_path: Output directory.
        ffmpeg_path: Optional FFmpeg executable path.
        is_playlist: Whether the task is a playlist.
        progress_hook: Progress callback.
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
        'home_path': save_path,  # Used by --paths home: as the base output directory.
        'progress_hooks': [progress_hook],
        'noplaylist': not is_playlist,
        'quiet': True,
        'no_warnings': True,
        'keepvideo': False,  # Important: delete source temporary files after merging.
    }
    
    # Dedicated temporary file directory (.ytdl_temp).
    temp_path = os.path.join(save_path, YTDL_TEMP_DIR)
    os.makedirs(temp_path, exist_ok=True)
    opts['temp_path'] = temp_path
    
    # Allow overwrites only when this is not a resume operation.
    # Keep .part files when resuming.
    if not is_resume:
        opts['overwrites'] = True
    
    if ffmpeg_path:
        opts['ffmpeg_location'] = ffmpeg_path
    else:
        log.warning("FFmpeg not found")
    
    return opts


@dataclass(frozen=True)
class AudioQualityProfile:
    source_format: str
    source_selectors: list[str]
    encoder_quality: str
    webm_recode_bitrate: str | None


def _build_audio_quality_profile(value):
    quality = str(value or DEFAULT_AUDIO_QUALITY).strip().lower()
    match = re.fullmatch(r'(\d+)\s*k?', quality)
    bitrate = match.group(1) if match else None

    if quality == 'worst':
        return AudioQualityProfile(
            source_format='worstaudio/worst',
            source_selectors=['worstaudio'],
            encoder_quality='10',
            webm_recode_bitrate='48k',
        )

    if bitrate:
        return AudioQualityProfile(
            source_format=FORMAT_BESTAUDIO,
            source_selectors=[f'bestaudio[abr<={bitrate}]', 'bestaudio'],
            encoder_quality=quality,
            webm_recode_bitrate=f'{bitrate}k',
        )

    return AudioQualityProfile(
        source_format=FORMAT_BESTAUDIO,
        source_selectors=['bestaudio'],
        encoder_quality='0' if quality == 'best' else quality,
        webm_recode_bitrate=None,
    )


def _combine_video_audio_format(video_selector, audio_selectors, fallback_selector):
    choices = [f'{video_selector}+{audio_selector}' for audio_selector in audio_selectors]
    choices.append(fallback_selector)
    return '/'.join(choices)


def _build_format_options(settings):
    """
    Build yt-dlp format options from the selected container, video quality,
    and audio quality settings.
    """
    opts = {}
    fmt = settings.get('format', DEFAULT_FORMAT)
    audio_profile = _build_audio_quality_profile(settings.get('audio_quality', DEFAULT_AUDIO_QUALITY))

    if fmt in AUDIO_FORMATS:
        audio_channels = settings.get('audio_channels', AUDIO_CHANNELS)
        opts.update({
            'format': audio_profile.source_format,
            'extract_audio': True,
            'audio_format': fmt,
            'audio_quality': audio_profile.encoder_quality,
            'postprocessor_args': {'ffmpeg': ['-ac', str(audio_channels)]}
        })
    else:
        q = settings.get('video_quality', DEFAULT_VIDEO_QUALITY)

        if q in ('best', 'worst'):
            video_selector = f'{q}video'
            opts['format'] = _combine_video_audio_format(video_selector, audio_profile.source_selectors, q)
        else:
            # Extract numeric height from values like '1080p'.
            height = ''.join(filter(str.isdigit, q))
            if height:
                video_selector = f'bestvideo[height<={height}]'
                fallback_selector = f'best[height<={height}]'
                opts['format'] = _combine_video_audio_format(
                    video_selector, audio_profile.source_selectors, fallback_selector
                )
            else:
                # Fall back to the default quality if parsing fails.
                fallback_quality = DEFAULT_VIDEO_QUALITY
                video_selector = f'{fallback_quality}video'
                opts['format'] = _combine_video_audio_format(
                    video_selector, audio_profile.source_selectors, fallback_quality
                )

        if fmt == 'webm':
            opts['recode_video'] = 'webm'
            if audio_profile.webm_recode_bitrate:
                opts['postprocessor_args'] = {'ffmpeg': ['-b:a', audio_profile.webm_recode_bitrate]}
        else:
            opts['merge_output_format'] = fmt

    return opts

def _build_postprocess_options(settings):
    """
    Build postprocess options, including audio normalization.
    
    Args:
        settings: Settings dictionary.
    
    Returns:
        Postprocess options dictionary.
    """
    opts = {}
    
    # Audio loudness normalization (loudnorm).
    if settings.get('normalize_audio'):
        pp_args = {'ffmpeg': ['-af', LOUDNORM_FILTER]}
        opts['postprocessor_args'] = pp_args
    
    return opts


def _build_advanced_options(settings):
    """
    Build advanced options for acceleration, cookies, and JavaScript runtime settings.
    
    Args:
        settings: Settings dictionary.
    
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
        if cookie_file_exists():
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


def _add_runtime_extract_options(opts: dict, settings: dict | None = None) -> dict:
    advanced_opts = _build_advanced_options(settings or {})
    for key in ("cookiefile", "js_runtimes"):
        if key in advanced_opts:
            opts[key] = advanced_opts[key]
    return opts


def _build_playlist_extract_options(settings: dict | None = None) -> dict:
    opts = {"extract_flat": True}
    return _add_runtime_extract_options(opts, settings)


def _build_metadata_extract_options(settings: dict | None = None, is_playlist: bool = False) -> dict:
    opts = {
        "extract_flat": "in_playlist",
        "noplaylist": not is_playlist,
    }

    if settings:
        opts.update(_build_format_options(settings))

    return _add_runtime_extract_options(opts, settings)

def _merge_postprocessor_args(existing_opts: dict, new_opts: dict) -> dict:
    """
    Merge postprocessor_args into existing yt-dlp options.
    
    Args:
        existing_opts: Existing options dictionary.
        new_opts: Newly added options dictionary.
    
    Returns:
        Merged options dictionary.
    """
    if 'postprocessor_args' not in new_opts:
        return existing_opts
    
    if 'postprocessor_args' in existing_opts:
        # Merge with existing postprocessor_args.
        existing_pp = existing_opts['postprocessor_args']
        new_pp = new_opts['postprocessor_args']
        if 'ffmpeg' in existing_pp and 'ffmpeg' in new_pp:
            existing_pp['ffmpeg'].extend(new_pp['ffmpeg'])
        else:
            existing_pp.update(new_pp)
    else:
        existing_opts.update(new_opts)
    
    return existing_opts


def _build_all_options(settings, save_path, ffmpeg_path, is_playlist, progress_hook, is_resume=False) -> dict:
    """Assemble the final yt-dlp options dictionary."""
    # Merge base options.
    ydl_opts = {}
    ydl_opts.update(_build_base_options(save_path, ffmpeg_path, is_playlist, progress_hook, settings, is_resume))
    ydl_opts.update(_build_format_options(settings))
    ydl_opts.update(_build_advanced_options(settings))
    
    # Merge postprocess options separately because postprocessor_args needs special handling.
    postprocess_opts = _build_postprocess_options(settings)
    ydl_opts = _merge_postprocessor_args(ydl_opts, postprocess_opts)
    
    return ydl_opts

# =====================================================================
# Generic download execution.
