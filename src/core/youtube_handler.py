"""
하위 호환성을 위한 리다이렉트 모듈
youtube_handler.py → download_handler.py로 이동되었습니다.
기존 import 경로를 유지하기 위해 모든 심볼을 re-export합니다.
"""
from core.download_handler import *  # noqa: F401, F403
from core.download_handler import (
    _sanitize_url,
    has_video_and_list,
    extract_playlist_video_ids,
    fetch_metadata,
    download_video,
    _build_base_options,
    _build_format_options,
    _build_postprocess_options,
    _build_advanced_options,
    _merge_postprocessor_args,
    _build_all_options,
)