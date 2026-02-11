"""
언어/로케일 관리 모듈
언어별 문자열을 로드하고 관리합니다.
"""
from typing import Dict
import os

# 지원하는 언어 목록
SUPPORTED_LANGUAGES = {
    'ko': '한국어',
    'ja': '日本語',
    'en': 'English'
}

# 기본 언어
DEFAULT_LANGUAGE = 'ko'

# 현재 언어 (런타임에 설정됨)
_current_language = DEFAULT_LANGUAGE
_strings: Dict[str, str] = {}


def set_language(lang_code: str):
    """언어를 설정합니다."""
    global _current_language, _strings
    
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    _current_language = lang_code
    _load_strings(lang_code)


def get_language() -> str:
    """현재 언어 코드를 반환합니다."""
    return _current_language


def get_string(key: str, default: str = None) -> str:
    """언어별 문자열을 가져옵니다."""
    return _strings.get(key, default or key)


def _load_strings(lang_code: str):
    """언어별 문자열을 로드합니다."""
    global _strings
    
    try:
        if lang_code == 'ko':
            from . import ko
            _strings = ko.STRINGS
        elif lang_code == 'ja':
            from . import ja
            _strings = ja.STRINGS
        elif lang_code == 'en':
            # 영어는 기본값이므로 별도 파일 로드 안함 (strings.py의 기본값 사용)
            _strings = {}
        else:
            # 지원하지 않는 언어는 한국어로 폴백 (또는 영어로 폴백하려면 {} 사용)
            from . import ko
            _strings = ko.STRINGS
    except ImportError:
        # 언어 파일을 찾을 수 없으면 빈 딕셔너리 사용 (기본값인 영어 출력)
        _strings = {}


# 초기화: 기본 언어 로드
_load_strings(DEFAULT_LANGUAGE)
