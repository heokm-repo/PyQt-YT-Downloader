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
    기본 yt-dlp 옵션 생성
    
    Args:
        save_path: 저장 경로
        ffmpeg_path: FFmpeg 경로 (None 가능)
        is_playlist: 플레이리스트 여부
        progress_hook: 진행률 훅 함수
        settings: 설정 딕셔너리 (선택적)
        is_resume: 이어받기 여부
    
    Returns:
        기본 옵션 딕셔너리
    """
    # 출력 템플릿은 settings에서 가져오되, 없으면 기본값 사용
    # [중요] outtmpl은 상대 경로만 사용 → --paths home: 과 함께 사용해야 --paths temp: 가 동작함
    output_template = settings.get('output_template', OUTPUT_TEMPLATE) if settings else OUTPUT_TEMPLATE
    
    opts = {
        'outtmpl': output_template,
        'home_path': save_path,  # --paths home: 용 (기본 저장 경로)
        'progress_hooks': [progress_hook],
        'noplaylist': not is_playlist,
        'quiet': True,
        'no_warnings': True,
        'keepvideo': False,  # [중요] 병합 후 원본(임시 파일) 삭제
    }
    
    # 임시 파일 전용 폴더 (.ytdl_temp)
    temp_path = os.path.join(save_path, YTDL_TEMP_DIR)
    os.makedirs(temp_path, exist_ok=True)
    opts['temp_path'] = temp_path
    
    # 이어받기(resume)가 아닐 때만 덮어쓰기 허용
    # resume일 때는 .part 파일을 유지하며 이어받기
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
    후처리 옵션 생성 (오디오 평준화 등)
    
    Args:
        settings: 설정 딕셔너리
    
    Returns:
        후처리 옵션 딕셔너리
    """
    opts = {}
    
    # 오디오 음량 평준화 (Loudnorm)
    if settings.get('normalize_audio'):
        pp_args = {'ffmpeg': ['-af', LOUDNORM_FILTER]}
        opts['postprocessor_args'] = pp_args
    
    return opts


def _build_advanced_options(settings):
    """
    고급 옵션 생성 (가속, 쿠키, JS 런타임 등)
    
    Args:
        settings: 설정 딕셔너리
    
    Returns:
        고급 옵션 딕셔너리
    """
    opts = {}
    
    # 가속 (멀티 스레드)
    if settings.get('use_acceleration'):
        concurrent_downloads = settings.get('concurrent_fragment_downloads', CONCURRENT_FRAGMENT_DOWNLOADS)
        opts['concurrent_fragment_downloads'] = concurrent_downloads
    
    # 인앱 로그인 쿠키 파일 사용
    try:
        from utils.cookie_store import get_cookie_file_path, cookie_file_exists
        if cookie_file_exists():
            cookie_path = get_cookie_file_path()
            opts['cookiefile'] = cookie_path
            log.info(f"Using cookie file: {cookie_path}")
    except ImportError:
        log.debug("cookie_store module not available, skipping cookie support")
    
    # QuickJS JS 런타임 경로 (yt-dlp 서명 풀기에 필요)
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
    후처리 옵션(postprocessor_args) 병합
    
    Args:
        existing_opts: 기존 옵션 딕셔너리
        new_opts: 새로 추가할 옵션 딕셔너리
    
    Returns:
        병합된 옵션 딕셔너리
    """
    if 'postprocessor_args' not in new_opts:
        return existing_opts
    
    if 'postprocessor_args' in existing_opts:
        # 기존 postprocessor_args와 병합
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
    """
    모든 옵션을 조립하여 최종 yt-dlp 옵션 딕셔너리 생성
    """
    # 기본 옵션들 병합
    ydl_opts = {}
    ydl_opts.update(_build_base_options(save_path, ffmpeg_path, is_playlist, progress_hook, settings, is_resume))
    ydl_opts.update(_build_format_options(settings))
    ydl_opts.update(_build_advanced_options(settings))
    
    # 후처리 옵션은 postprocessor_args 병합이 필요하므로 별도 처리
    postprocess_opts = _build_postprocess_options(settings)
    ydl_opts = _merge_postprocessor_args(ydl_opts, postprocess_opts)
    
    return ydl_opts

# =====================================================================
# 다운로드 실행 (범용)
