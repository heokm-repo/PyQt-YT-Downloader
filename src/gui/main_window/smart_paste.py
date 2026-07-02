"""Helpers for deciding whether clipboard text should start a download."""

from typing import Optional

from utils.utils import validate_url


def extract_valid_clipboard_url(text: Optional[str]) -> str:
    """Return a stripped URL from clipboard text, or an empty string if invalid."""
    stripped = (text or "").strip()
    if stripped and validate_url(stripped):
        return stripped
    return ""