"""Apply localized text to the main window controls."""

from dataclasses import dataclass
from typing import Any

from gui.widgets.button_sizing import set_text_button_minimum_width
from resources.styles import DOWNLOAD_BUTTON_WIDTH_PADDING


@dataclass(frozen=True)
class MainWindowLanguageTexts:
    title: str
    url_placeholder: str
    download_text: str
    empty_text: str
    ready_text: str


def update_download_button_text(button: Any, text: str) -> int:
    """Set download-button text and resize its minimum width to fit."""
    button.setText(text)
    return set_text_button_minimum_width(button, DOWNLOAD_BUTTON_WIDTH_PADDING)


def apply_main_window_language(window: Any, texts: MainWindowLanguageTexts, has_tasks: bool) -> None:
    """Apply localized labels to controls that have already been created."""
    window.setWindowTitle(texts.title)

    if hasattr(window, "app_title_label"):
        window.app_title_label.setText(texts.title)
    if hasattr(window, "url_input"):
        window.url_input.setPlaceholderText(texts.url_placeholder)
    if hasattr(window, "download_btn"):
        update_download_button_text(window.download_btn, texts.download_text)
    if hasattr(window, "empty_label"):
        window.empty_label.setText(texts.empty_text)
    if hasattr(window, "status_label") and not has_tasks:
        window.status_label.setText(texts.ready_text)