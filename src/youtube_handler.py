import os
import yt_dlp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from utils import get_ffmpeg_path
from logger import log
from constants import (
    ERROR_INVALID_URL, MSG_DOWNLOAD_COMPLETE, MSG_PAUSED_BY_USER, DEFAULT_VIDEO_QUALITY,
    MSG_NOT_PLAYLIST_URL, MSG_CANNOT_FETCH_INFO,
    DEFAULT_PLAYLIST_TITLE, DEFAULT_UPLOADER, DEFAULT_VIDEO_TITLE,
    CONCURRENT_FRAGMENT_DOWNLOADS, LOUDNORM_FILTER, OUTPUT_TEMPLATE, AUDIO_CHANNELS,
    FORMAT_MP3, FORMAT_BESTAUDIO, DEFAULT_FORMAT,
    YOUTUBE_PLAYLIST_URL_PREFIX, YOUTUBE_SHORTS_PATH,
    COOKIES_BROWSER_DEFAULT
)

def _sanitize_url(url, prefer_playlist=False):
    """
    URL 정제 및 플레이리스트/비디오 구분 로직 간소화
    """
    if not url: return "", False
    
    # 문자열 변환 (안전장치)
    url = str(url)
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)

    # 공통 플래그 계산
    is_short_url = parsed.netloc.endswith('youtu.be')
    has_path_video = (
        is_short_url and parsed.path and parsed.path != '/' 
        and not parsed.path.startswith(YOUTUBE_SHORTS_PATH)
    )
    has_v_param = 'v' in qs
    has_video = has_v_param or has_path_video
    
    # 1. 숏츠는 무조건 단일 영상 처리
    if parsed.path and YOUTUBE_SHORTS_PATH in parsed.path:
        return url, False
    
    # 2. 영상(v 또는 youtu.be 경로)과 리스트(list)가 같이 있는 경우
    if has_video and 'list' in qs:
        if prefer_playlist:
            # 리스트 모드: v 제거 -> 플레이리스트 URL 생성
            return f"{YOUTUBE_PLAYLIST_URL_PREFIX}{qs['list'][0]}", True
        else:
            # 영상 모드: list 제거 -> 순수 영상 URL 재조립
            del qs['list']
            new_query = urlencode(qs, doseq=True)
            return urlunparse(parsed._replace(query=new_query)), False

    # 3. 순수 플레이리스트 (v 없고 list 있음)
    if 'list' in qs and not has_video:
        return url, True

    # 그 외 일반 영상
    return url, False

def has_video_and_list(url):
    """URL에 v와 list가 동시에 존재하는지 확인"""
    if not url: return False
    parsed = urlparse(str(url))
    qs = parse_qs(parsed.query)
    
    is_short_url = parsed.netloc.endswith('youtu.be')
    has_path_video = (
        is_short_url and parsed.path and parsed.path != '/' 
        and not (parsed.path or "").startswith(YOUTUBE_SHORTS_PATH)
    )
    has_v_param = 'v' in qs
    has_video = has_v_param or has_path_video

    return has_video and 'list' in qs and YOUTUBE_SHORTS_PATH not in (parsed.path or "")

def extract_playlist_video_ids(url):
    """플레이리스트 ID 추출 (경량화)"""
    clean_url, is_playlist = _sanitize_url(url, prefer_playlist=True)
    
    if not is_playlist:
        return [], False, MSG_NOT_PLAYLIST_URL
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': True, # 메타데이터 없이 ID만 빠르게 추출
        'ignoreerrors': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            data = ydl.extract_info(clean_url, download=False)
            if not data or 'entries' not in data:
                return [], False, MSG_CANNOT_FETCH_INFO
            
            # 유효한 ID만 필터링
            ids = [e['id'] for e in data['entries'] if e and e.get('id')]
            return ids, True, ""
            
    except Exception as e:
        log.error(f"Playlist Error: {e}")
        return [], False, str(e)

def fetch_metadata(url, settings=None):
    """영상 메타데이터 조회 (실제 다운로드 포맷 기준으로 크기 추정)"""
    clean_url, is_playlist = _sanitize_url(url)
    if not clean_url: return {}, False

    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist',
        'noplaylist': not is_playlist,
    }
    
    # 설정이 있으면 실제 다운로드 시 사용할 포맷 옵션 적용
    if settings:
        format_opts = _build_format_options(settings)
        ydl_opts.update(format_opts)
    else:
        # 설정이 없으면 기본값 사용
        default_quality = DEFAULT_VIDEO_QUALITY
        ydl_opts['format'] = f'{default_quality}video+{default_quality}audio/best'
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            if not info: return {}, False
            
            # 플레이리스트 메타데이터
            if is_playlist:
                return {
                    'title': info.get('title', DEFAULT_PLAYLIST_TITLE),
                    'uploader': info.get('uploader', DEFAULT_UPLOADER),
                    'is_playlist': True,
                    'video_count': len(info.get('entries', []))
                }, True

            # 단일 영상 (플레이리스트 내부 항목일 경우 첫 번째 항목 사용)
            if 'entries' in info:
                info = info['entries'][0]

            # 실제 다운로드 시 사용될 포맷의 크기 추정
            video_size = 0
            audio_size = 0
            
            # requested_formats에 실제 선택된 포맷 정보가 있음
            if 'requested_formats' in info:
                for f in info['requested_formats']:
                    size = f.get('filesize', 0) or f.get('filesize_approx', 0)
                    if f.get('vcodec') != 'none':
                        video_size = size
                    elif f.get('acodec') != 'none':
                        audio_size = size
            else:
                # 단일 파일인 경우 (requested_formats가 없는 경우)
                size = info.get('filesize', 0) or info.get('filesize_approx', 0)
                if info.get('vcodec') != 'none':
                    video_size = size
                elif info.get('acodec') != 'none':
                    audio_size = size
            
            # requested_formats가 없거나 크기를 알 수 없는 경우 fallback
            if video_size == 0 and audio_size == 0:
                formats = info.get('formats', [])
                video_size = max([f.get('filesize', 0) or f.get('filesize_approx', 0) 
                                for f in formats if f.get('vcodec') != 'none'], default=0)
                audio_size = max([f.get('filesize', 0) or f.get('filesize_approx', 0) 
                                for f in formats if f.get('acodec') != 'none'], default=0)

            return {
                'title': info.get('title', DEFAULT_VIDEO_TITLE),
                'uploader': info.get('uploader', info.get('channel', DEFAULT_UPLOADER)),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail'),
                'id': info.get('id'),
                'webpage_url': info.get('webpage_url', clean_url),
                'video_size': video_size,
                'audio_size': audio_size
            }, True
    except Exception as e:
        log.error(f"Metadata Error: {e}")
        return {}, False

def _build_base_options(save_path, ffmpeg_path, is_playlist, progress_hook, settings=None):
    """
    기본 yt-dlp 옵션 생성
    
    Args:
        save_path: 저장 경로
        ffmpeg_path: FFmpeg 경로 (None 가능)
        is_playlist: 플레이리스트 여부
        progress_hook: 진행률 훅 함수
        settings: 설정 딕셔너리 (선택적)
    
    Returns:
        기본 옵션 딕셔너리
    """
    # 출력 템플릿은 settings에서 가져오되, 없으면 기본값 사용
    output_template = settings.get('output_template', OUTPUT_TEMPLATE) if settings else OUTPUT_TEMPLATE
    output_tmpl = os.path.join(save_path, output_template)
    
    opts = {
        'outtmpl': output_tmpl,
        'progress_hooks': [progress_hook],
        'noplaylist': not is_playlist,
        'quiet': True,
        'no_warnings': True,
        'keepvideo': False,  # [중요] 병합 후 원본(임시 파일) 삭제
        'overwrites': True,
    }
    
    if ffmpeg_path:
        opts['ffmpeg_location'] = ffmpeg_path
    else:
        log.warning("FFmpeg not found")
    
    return opts


def _build_format_options(settings):
    """
    포맷 및 품질 관련 옵션 생성
    
    Args:
        settings: 설정 딕셔너리
    
    Returns:
        포맷 옵션 딕셔너리
    """
    opts = {}
    fmt = settings.get('format', DEFAULT_FORMAT)
    
    if fmt == FORMAT_MP3:
        # 오디오 채널 수는 settings에서 가져오되, 없으면 기본값 사용
        audio_channels = settings.get('audio_channels', AUDIO_CHANNELS)
        opts.update({
            'format': FORMAT_BESTAUDIO,
            'extract_audio': True,
            'audio_format': FORMAT_MP3,
            'postprocessor_args': {'ffmpeg': ['-ac', str(audio_channels)]}
        })
    else:
        opts['merge_output_format'] = fmt
        q = settings.get('video_quality', DEFAULT_VIDEO_QUALITY)
        
        if q in ('best', 'worst'):
            opts['format'] = f'{q}video+{q}audio/best'
        else:
            # '1080p' 등에서 숫자만 추출
            height = ''.join(filter(str.isdigit, q))
            if height:
                opts['format'] = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
            else:
                # 파싱 실패 시 기본값 사용 (설정 무시 방지)
                fallback_quality = DEFAULT_VIDEO_QUALITY
                opts['format'] = f'{fallback_quality}video+{fallback_quality}audio/best'
    
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
    고급 옵션 생성 (가속, 쿠키 등)
    
    Args:
        settings: 설정 딕셔너리
    
    Returns:
        고급 옵션 딕셔너리
    """
    opts = {}
    
    # 가속 (멀티 스레드)
    if settings.get('use_acceleration'):
        # 동시 다운로드 스레드 수는 settings에서 가져오되, 없으면 기본값 사용
        concurrent_downloads = settings.get('concurrent_fragment_downloads', CONCURRENT_FRAGMENT_DOWNLOADS)
        opts['concurrent_fragment_downloads'] = concurrent_downloads
    
    # 쿠키 브라우저 설정 기능은 비활성화됨 (설정 다이얼로그에서 제거)
    return opts


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


def _build_all_options(settings, save_path, ffmpeg_path, is_playlist, progress_hook) -> dict:
    """
    모든 옵션을 조립하여 최종 yt-dlp 옵션 딕셔너리 생성
    
    Args:
        settings: 설정 딕셔너리
        save_path: 저장 경로
        ffmpeg_path: FFmpeg 경로
        is_playlist: 플레이리스트 여부
        progress_hook: 진행률 훅 함수
    
    Returns:
        완성된 yt-dlp 옵션 딕셔너리
    """
    # 기본 옵션들 병합
    ydl_opts = {}
    ydl_opts.update(_build_base_options(save_path, ffmpeg_path, is_playlist, progress_hook, settings))
    ydl_opts.update(_build_format_options(settings))
    ydl_opts.update(_build_advanced_options(settings))
    
    # 후처리 옵션은 postprocessor_args 병합이 필요하므로 별도 처리
    postprocess_opts = _build_postprocess_options(settings)
    ydl_opts = _merge_postprocessor_args(ydl_opts, postprocess_opts)
    
    return ydl_opts


def download_video(url, settings, progress_hook):
    """
    영상 다운로드 핵심 로직
    - keepvideo: False 설정으로 임시 파일 삭제 문제 해결
    """
    if not url: 
        return False, ERROR_INVALID_URL

    clean_url, is_playlist = _sanitize_url(url)
    
    # 저장 경로 설정
    save_path = settings.get('download_folder') or settings.get('save_path') or os.getcwd()
    ffmpeg_path = get_ffmpeg_path()
    
    # 모든 옵션 조립
    ydl_opts = _build_all_options(settings, save_path, ffmpeg_path, is_playlist, progress_hook)

    # 다운로드 실행
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([clean_url])
        return True, MSG_DOWNLOAD_COMPLETE
    except Exception as e:
        error_msg = str(e)
        # 사용자가 일시정지 버튼을 누른 경우 (workers.py에서 발생시킨 예외)
        if MSG_PAUSED_BY_USER in error_msg:
            return False, MSG_PAUSED_BY_USER
            
        log.error(f"Download Error: {error_msg}")
        return False, error_msg