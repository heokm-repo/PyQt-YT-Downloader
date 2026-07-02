"""Convenience helpers for MessageDialog-based prompts."""

from typing import Any

from PyQt5.QtWidgets import QDialog

from gui.dialogs.message_dialog import MessageDialog


def _dialog_factory(dialog_factory: Any | None) -> Any:
    return dialog_factory if dialog_factory is not None else MessageDialog


def show_message(
    parent: Any,
    title: str,
    message: str,
    dialog_type: str,
    dialog_factory: Any | None = None,
    **kwargs: Any,
) -> Any:
    """Show a MessageDialog-compatible dialog and return the instance."""
    factory = _dialog_factory(dialog_factory)
    dialog = factory(title, message, dialog_type, parent, **kwargs)
    dialog.exec_()
    return dialog


def show_info(
    parent: Any,
    title: str,
    message: str,
    dialog_factory: Any | None = None,
) -> Any:
    factory = _dialog_factory(dialog_factory)
    return show_message(parent, title, message, factory.INFO, factory)


def show_warning(
    parent: Any,
    title: str,
    message: str,
    dialog_factory: Any | None = None,
) -> Any:
    factory = _dialog_factory(dialog_factory)
    return show_message(parent, title, message, factory.WARNING, factory)


def show_error(
    parent: Any,
    title: str,
    message: str,
    dialog_factory: Any | None = None,
) -> Any:
    factory = _dialog_factory(dialog_factory)
    return show_message(parent, title, message, factory.ERROR, factory)


def ask_question(
    parent: Any,
    title: str,
    message: str,
    dialog_factory: Any | None = None,
    accepted_result: int = QDialog.Accepted,
    show_cancel: bool = False,
) -> bool:
    """Ask a yes/no-style question and return True when accepted."""
    factory = _dialog_factory(dialog_factory)
    dialog = factory(
        title,
        message,
        factory.QUESTION,
        parent,
        show_cancel=show_cancel,
    )
    return dialog.exec_() == accepted_result


def ask_custom_question(
    parent: Any,
    title: str,
    message: str,
    buttons: list[dict[str, Any]],
    dialog_factory: Any | None = None,
) -> int | None:
    """Ask a question with custom buttons and return the clicked button index."""
    factory = _dialog_factory(dialog_factory)
    dialog = factory(title, message, factory.QUESTION, parent, buttons=buttons)
    dialog.exec_()
    return getattr(dialog, "clicked_button_index", None)