"""Message dialog helpers for main-window workflows."""

from gui.dialogs.messages import ask_custom_question, ask_question, show_info, show_warning


def playlist_error_text(error_msg: str, fallback_message: str) -> str:
    """Return the visible playlist error text."""
    return error_msg if error_msg else fallback_message


def show_playlist_error_dialog(
    parent,
    title: str,
    error_msg: str,
    fallback_message: str,
    dialog_factory=None,
) -> str:
    """Show the playlist error dialog and return the text shown."""
    message = playlist_error_text(error_msg, fallback_message)
    show_warning(parent, title, message, dialog_factory)
    return message


def ask_duplicate_confirmation_dialog(
    parent,
    total_count: int,
    duplicate_count: int,
    title: str,
    message_template: str,
    dialog_factory=None,
) -> bool:
    """Ask whether duplicate playlist items should be excluded."""
    return ask_question(
        parent,
        title,
        message_template.format(total=total_count, duplicate=duplicate_count),
        dialog_factory,
    )


def confirm_duplicate_overwrite_dialog(
    parent,
    title: str,
    message: str,
    dialog_factory=None,
) -> bool:
    """Ask whether an existing duplicate should be overwritten."""
    return ask_question(parent, title, message, dialog_factory)


def show_no_new_videos_dialog(
    parent,
    title: str,
    message: str,
    dialog_factory=None,
) -> None:
    """Show a notification when no playlist items remain to register."""
    show_info(parent, title, message, dialog_factory)


def confirm_resume_paused_tasks_dialog(
    parent,
    title: str,
    message: str,
    dialog_factory=None,
) -> bool:
    """Ask whether paused tasks loaded from disk should be resumed."""
    return ask_question(parent, title, message, dialog_factory)


def ask_playlist_video_preference(
    parent,
    title: str,
    message: str,
    playlist_text: str,
    video_text: str,
    cancel_text: str,
    dialog_factory=None,
) -> bool | None:
    """Ask whether a mixed YouTube URL should use the playlist or current video."""
    clicked_button_index = ask_custom_question(
        parent,
        title,
        message,
        [
            {"text": playlist_text, "role": "action"},
            {"text": video_text, "role": "action"},
            {"text": cancel_text, "role": "reject"},
        ],
        dialog_factory,
    )
    if clicked_button_index == 0:
        return True
    if clicked_button_index == 1:
        return False
    return None


def show_invalid_url_dialog(parent, title: str, message: str, dialog_factory=None) -> None:
    """Show an invalid URL warning."""
    show_warning(parent, title, message, dialog_factory)