"""Binary installation and binary update startup flow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from locales.strings import STR


@dataclass(frozen=True)
class StartupCheckResult:
    updates_available: dict
    app_update_info: tuple[bool, str | None, str | None, str | None]
    check_failed: bool = False
    error_message: str | None = None


def load_startup_language(logger: Any) -> None:
    """Load saved settings early so startup dialogs use the selected language."""
    try:
        from utils.settings_store import load_settings
        from constants import KEY_LANGUAGE, change_language
        from locales import DEFAULT_LANGUAGE

        settings = load_settings()
        language = settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE)
        change_language(language)
        logger.info(f"Loaded language early: {language}")
    except Exception as exc:
        logger.warning(f"Failed to load language setting early: {exc}")


def run_startup_checks(dialog_factory: Callable[[], Any] | None = None) -> StartupCheckResult:
    """Run the startup dialog checks and return their collected update data."""
    if dialog_factory is None:
        from gui.dialogs.startup_dialog import StartupDialog

        dialog_factory = StartupDialog

    startup_dialog = dialog_factory()
    startup_dialog.show()
    startup_dialog.start_checks()
    startup_dialog.exec_()
    return StartupCheckResult(
        updates_available=getattr(startup_dialog, "updates_available", {}),
        app_update_info=getattr(
            startup_dialog,
            "app_update_info",
            (False, None, None, None),
        ),
        check_failed=getattr(startup_dialog, "check_failed", False),
        error_message=getattr(startup_dialog, "check_error", None),
    )


def format_binary_update_message(updates: dict, header: str, ask_now: str) -> str:
    """Build the visible update prompt for external binary updates."""
    message = header
    for name, info in updates.items():
        display_name = "FFmpeg / ffprobe" if name == "ffmpeg" else name
        message += (
            f"\u2022 {display_name}: "
            f"{info['current']} \u2192 {info['latest']}\n"
        )
    return message + ask_now


def run_initial_binary_install(
    accepted_result: int,
    show_error_message: Callable[[str, str, str], None],
    logger: Any,
    binary_names: tuple[str, ...] | None = None,
    setup_dialog_factory: Callable[[], Any] | None = None,
    progress_dialog_factory: Callable[..., Any] | None = None,
) -> None:
    """Run first-launch setup and required binary download."""
    if setup_dialog_factory is None:
        from gui.dialogs.init_setup_dialog import InitSetupDialog

        setup_dialog_factory = InitSetupDialog
    if progress_dialog_factory is None:
        from gui.dialogs.download_progress_dialog import DownloadProgressDialog

        progress_dialog_factory = DownloadProgressDialog

    setup_dialog = setup_dialog_factory()
    if setup_dialog.exec_() != accepted_result:
        raise SystemExit(0) from None

    from locales import get_language

    logger.info(f"Initial setup completed. Language: {get_language()}")
    logger.info("Binaries not found. Starting initial download...")

    progress_dialog = progress_dialog_factory(binary_names=binary_names)
    progress_dialog.exec_()
    if not progress_dialog.download_success:
        show_error_message(
            STR.TITLE_INIT_FAIL,
            STR.ERR_DL_COMPONENT_FAIL,
            STR.MSG_CHECK_NET,
        )
        raise SystemExit(1) from None

    logger.info("Initial binary download completed successfully")


def run_missing_binary_repair(
    binary_names: tuple[str, ...],
    show_error_message: Callable[[str, str, str], None],
    logger: Any,
    progress_dialog_factory: Callable[..., Any] | None = None,
) -> None:
    """Repair only missing managed binaries without repeating first-run setup."""
    if not binary_names:
        return
    if progress_dialog_factory is None:
        from gui.dialogs.download_progress_dialog import DownloadProgressDialog

        progress_dialog_factory = DownloadProgressDialog

    logger.info(
        f"Repairing missing managed binaries: {', '.join(binary_names)}"
    )
    progress_dialog = progress_dialog_factory(binary_names=binary_names)
    progress_dialog.exec_()
    if progress_dialog.download_success:
        logger.info("Missing binary repair completed successfully")
        return

    show_error_message(
        STR.TITLE_INIT_FAIL,
        STR.ERR_DL_COMPONENT_FAIL,
        STR.MSG_CHECK_NET,
    )
    raise SystemExit(1) from None


def run_binary_update_prompt(
    updates: dict,
    accepted_result: int,
    logger: Any,
    message_dialog_factory: Callable[..., Any] | None = None,
    progress_dialog_factory: Callable[..., Any] | None = None,
) -> None:
    """Prompt for and optionally run external binary updates."""
    if not updates:
        logger.info("All binaries are up to date")
        return

    if message_dialog_factory is None:
        from gui.dialogs.message_dialog import MessageDialog

        message_dialog_factory = MessageDialog
    if progress_dialog_factory is None:
        from gui.dialogs.download_progress_dialog import DownloadProgressDialog

        progress_dialog_factory = DownloadProgressDialog

    update_message = format_binary_update_message(
        updates,
        STR.MSG_UPDATE_COMPONENTS,
        STR.MSG_UPDATE_ASK_NOW,
    )
    dialog = message_dialog_factory(
        STR.TITLE_UPDATE_CHECK,
        update_message,
        message_dialog_factory.QUESTION,
        show_cancel=False,
    )
    if dialog.exec_() != accepted_result:
        logger.info("User skipped updates")
        return

    logger.info("User chose to update binaries")
    progress_dialog = progress_dialog_factory(update_mode=True, updates=updates)
    progress_dialog.exec_()
    if progress_dialog.download_success:
        logger.info("Update completed successfully")
    else:
        logger.warning("Update failed or cancelled")


def run_startup_binary_flow(
    accepted_result: int,
    show_error_message: Callable[[str, str, str], None],
    logger: Any,
) -> tuple[bool, str | None, str | None, str | None]:
    """Run startup language, external binary checks, and binary updates."""
    from utils.bin.manager import (
        check_binary_presence,
        missing_binary_downloads,
    )

    load_startup_language(logger)
    startup_result = run_startup_checks()

    presence = check_binary_presence()
    if all(presence.values()):
        if startup_result.check_failed:
            message = "Startup update checks did not complete"
            if startup_result.error_message:
                message += f": {startup_result.error_message}"
            logger.warning(message)
        else:
            run_binary_update_prompt(
                startup_result.updates_available,
                accepted_result,
                logger,
            )
    else:
        binary_names = missing_binary_downloads(presence)
        if any(presence.values()):
            run_missing_binary_repair(
                binary_names,
                show_error_message,
                logger,
            )
        else:
            run_initial_binary_install(
                accepted_result,
                show_error_message,
                logger,
                binary_names=binary_names,
            )

    return startup_result.app_update_info
