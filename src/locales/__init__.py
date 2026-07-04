"""Language and locale management for loading localized strings."""
from typing import Dict
import os

# Supported languages.
SUPPORTED_LANGUAGES = {
    'ko': '한국어',
    'ja': '日本語',
    'en': 'English'
}

# Default language.
DEFAULT_LANGUAGE = 'en'

# Current language, set at runtime.
_current_language = DEFAULT_LANGUAGE
_strings: Dict[str, str] = {}


def set_language(lang_code: str):
    """Set the active language."""
    global _current_language
    
    if lang_code not in SUPPORTED_LANGUAGES:
        lang_code = DEFAULT_LANGUAGE
    
    _current_language = lang_code
    _load_strings(lang_code)


def get_language() -> str:
    """Return the current language code."""
    return _current_language


def get_string(key: str, default: str = None) -> str:
    """Return a localized string."""
    return _strings.get(key, default or key)


def _load_strings(lang_code: str):
    """Load strings for a language."""
    global _strings
    
    try:
        if lang_code == 'ko':
            from . import ko
            _strings = ko.STRINGS
        elif lang_code == 'ja':
            from . import ja
            _strings = ja.STRINGS
        elif lang_code == 'en':
            # English uses defaults, so no separate file is loaded.
            _strings = {}
        else:
            # Unsupported languages fall back to Korean.
            from . import ko
            _strings = ko.STRINGS
    except ImportError:
        # If the language file is missing, use an empty dict and fall back to English defaults.
        _strings = {}


# Initialization: load the default language.
_load_strings(DEFAULT_LANGUAGE)
