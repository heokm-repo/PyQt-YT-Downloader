"""Helpers for text buttons with localized labels."""

from typing import Any

from resources.styles import TEXT_BUTTON_WIDTH_PADDING


def text_button_minimum_width(
    button: Any,
    padding: int = TEXT_BUTTON_WIDTH_PADDING,
) -> int:
    """Return the minimum width needed for the button's current text."""
    text_width = button.fontMetrics().boundingRect(button.text()).width()
    return text_width + padding


def set_text_button_minimum_width(
    button: Any,
    padding: int = TEXT_BUTTON_WIDTH_PADDING,
) -> int:
    """Resize a text button's minimum width and return the applied width."""
    width = text_button_minimum_width(button, padding)
    button.setMinimumWidth(width)
    return width