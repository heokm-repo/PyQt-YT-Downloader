"""Convert settings dialog form values into settings dictionaries."""

from typing import Any, Mapping

from constants import (
    KEY_AUDIO_QUALITY,
    KEY_DOWNLOAD_FOLDER,
    KEY_FORMAT,
    KEY_LANGUAGE,
    KEY_MAX_DOWNLOADS,
    KEY_NORMALIZE_AUDIO,
    KEY_USE_ACCELERATION,
    KEY_UNIVERSAL_COMPATIBILITY,
    KEY_VIDEO_QUALITY,
)
from locales import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


def normalize_download_folder_input(folder_text: Any) -> str:
    """Return a stripped download-folder value from a form field."""
    if folder_text is None:
        return ""
    return str(folder_text).strip()


def is_download_folder_input_valid(folder_text: Any) -> bool:
    """Return True when the folder field has a non-empty value."""
    return bool(normalize_download_folder_input(folder_text))


def language_display_options(
    supported_languages: Mapping[str, str] = SUPPORTED_LANGUAGES,
) -> list[str]:
    """Return combo-box labels for supported languages."""
    return [f"{code} - {name}" for code, name in supported_languages.items()]


def language_index_for_code(
    language_code: str | None,
    supported_languages: Mapping[str, str] = SUPPORTED_LANGUAGES,
) -> int:
    """Return the combo-box index for a language code, or 0 when unknown."""
    language_codes = list(supported_languages.keys())
    if language_code in language_codes:
        return language_codes.index(language_code)
    return 0


def language_code_at_index(
    index: int,
    supported_languages: Mapping[str, str] = SUPPORTED_LANGUAGES,
    default_language: str = DEFAULT_LANGUAGE,
) -> str:
    """Return the language code at a combo-box index, or the default language."""
    language_codes = list(supported_languages.keys())
    if 0 <= index < len(language_codes):
        return language_codes[index]
    return default_language


def build_settings_from_form_values(
    current_settings: Mapping[str, Any],
    folder_path: str,
    video_quality: str,
    audio_quality: str,
    output_format: str,
    normalize_audio: bool,
    use_acceleration: bool,
    max_downloads: int,
    language_index: int,
    universal_compatibility: bool = False,
) -> dict[str, Any]:
    """Return updated settings from the current dialog form values."""
    settings = dict(current_settings)
    settings[KEY_DOWNLOAD_FOLDER] = folder_path
    settings[KEY_VIDEO_QUALITY] = video_quality
    settings[KEY_AUDIO_QUALITY] = audio_quality
    settings[KEY_FORMAT] = output_format
    settings[KEY_NORMALIZE_AUDIO] = normalize_audio
    settings[KEY_USE_ACCELERATION] = use_acceleration
    settings[KEY_UNIVERSAL_COMPATIBILITY] = universal_compatibility
    settings[KEY_MAX_DOWNLOADS] = max_downloads
    settings[KEY_LANGUAGE] = language_code_at_index(language_index)
    return settings
