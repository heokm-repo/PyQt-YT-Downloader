"""Message helpers for settings fallback notices."""

from typing import Any

from gui.dialogs.messages import show_warning


def build_download_folder_fallback_message(template: str, notice: Any) -> str:
    """Format the notice shown when the configured download folder changes."""
    return template.format(
        old_path=notice.original_path,
        new_path=notice.fallback_path,
        reason=notice.reason,
    )


def show_download_folder_fallback_notice(
    parent: Any,
    notice: Any,
    title: str,
    message_template: str,
    dialog_factory: Any | None = None,
) -> str:
    """Show a message dialog for a download-folder fallback notice."""
    message = build_download_folder_fallback_message(message_template, notice)
    show_warning(parent, title, message, dialog_factory)
    return message