"""Application self-update startup flow."""
from __future__ import annotations

from typing import Any, Callable

from locales.strings import STR


def prompt_for_app_update(
    latest_version: str | None,
    accepted_result: int,
    message_dialog_factory: Callable[..., Any] | None = None,
) -> bool:
    """Ask whether the available application update should be installed."""
    if message_dialog_factory is None:
        from gui.dialogs.message_dialog import MessageDialog

        message_dialog_factory = MessageDialog

    import constants

    message = STR.MSG_UPDATE_AVAILABLE.format(
        current=constants.APP_VERSION,
        latest=latest_version,
    )
    dialog = message_dialog_factory(
        STR.TITLE_APP_UPDATE,
        message,
        message_dialog_factory.QUESTION,
    )
    return dialog.exec_() == accepted_result


def download_app_update(
    download_url: str,
    download_update: Callable[[str, Callable[[int], None]], str | None],
    application: Any,
    logger: Any,
    progress_dialog_factory: Callable[..., Any] | None = None,
    parent: Any = None,
) -> str | None:
    """Download an app update while showing a styled progress dialog."""
    if progress_dialog_factory is None:
        from gui.dialogs.app_update_progress_dialog import AppUpdateProgressDialog

        progress_dialog_factory = AppUpdateProgressDialog

    progress = progress_dialog_factory(parent=parent)
    progress.show()

    def process_events() -> None:
        process_events_func = getattr(application, "processEvents", None)
        if process_events_func:
            process_events_func()

    def update_progress(percent: int) -> None:
        progress.set_progress(percent)
        process_events()
        if progress.was_cancelled():
            raise RuntimeError("Cancelled by user")

    try:
        try:
            result = download_update(download_url, update_progress)
            if result:
                progress.mark_installing()
                process_events()
            return result
        except Exception as exc:
            logger.warning(f"Update download cancelled or failed: {exc}")
            return None
    finally:
        progress.close()


def run_app_update_flow(
    app_update_info: tuple[bool, str | None, str | None],
    accepted_result: int,
    application: Any,
    show_error_message: Callable[[str, str], None],
    logger: Any,
) -> None:
    """Handle an available application self-update."""
    update_available, latest_version, download_url = app_update_info
    if not update_available:
        return

    try:
        from utils.app_updater import apply_update, download_update

        if not prompt_for_app_update(latest_version, accepted_result):
            return

        new_exe = download_app_update(download_url, download_update, application, logger)
        if not new_exe:
            logger.info("App update download did not produce an installer")
            return

        if apply_update(new_exe):
            raise SystemExit(0) from None

        show_error_message(STR.TITLE_ERROR, STR.ERR_UPDATE_APPLY)
    except SystemExit:
        raise
    except Exception as exc:
        logger.error(f"App update check failed: {exc}")
        show_error_message(STR.TITLE_ERROR, STR.ERR_UPDATE_CHECK.format(error=exc))
