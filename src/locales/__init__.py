"""Language and locale management for loading localized strings."""
from typing import Dict

# Supported languages.
SUPPORTED_LANGUAGES = {
    'de': 'Deutsch',
    'en': 'English',
    'es': 'Español',
    'fr': 'Français',
    'id': 'Bahasa Indonesia',
    'it': 'Italiano',
    'ja': '日本語',
    'ko': '한국어',
    'pl': 'Polski',
    'pt-BR': 'Português (Brasil)',
    'ru': 'Русский',
    'th': 'ไทย',
    'tr': 'Türkçe',
    'vi': 'Tiếng Việt',
    'zh-CN': '简体中文',
    'zh-TW': '繁體中文（台灣）',
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
        elif lang_code == 'zh-CN':
            from . import zh_cn
            _strings = zh_cn.STRINGS
        elif lang_code == 'es':
            from . import es
            _strings = es.STRINGS
        elif lang_code == 'pt-BR':
            from . import pt_br
            _strings = pt_br.STRINGS
        elif lang_code == 'de':
            from . import de
            _strings = de.STRINGS
        elif lang_code == 'fr':
            from . import fr
            _strings = fr.STRINGS
        elif lang_code == 'id':
            from . import id
            _strings = id.STRINGS
        elif lang_code == 'vi':
            from . import vi
            _strings = vi.STRINGS
        elif lang_code == 'ru':
            from . import ru
            _strings = ru.STRINGS
        elif lang_code == 'zh-TW':
            from . import zh_tw
            _strings = zh_tw.STRINGS
        elif lang_code == 'th':
            from . import th
            _strings = th.STRINGS
        elif lang_code == 'tr':
            from . import tr
            _strings = tr.STRINGS
        elif lang_code == 'it':
            from . import it
            _strings = it.STRINGS
        elif lang_code == 'pl':
            from . import pl
            _strings = pl.STRINGS
    except ImportError:
        # If the language file is missing, use an empty dict and fall back to English defaults.
        _strings = {}


# Initialization: load the default language.
_load_strings(DEFAULT_LANGUAGE)
