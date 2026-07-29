"""Background worker for settings-triggered update checks."""

from __future__ import annotations

from typing import Callable, Mapping

from PyQt5.QtCore import QObject, QThread, pyqtSignal

from gui.settings.settings_update_check import UpdateCheckSummary, run_update_check
from utils.logger import log
from utils.url_security import redact_urls_in_text


AppUpdateChecker = Callable[
    [],
    tuple[bool, str | None, str | None, str | None],
]
BinaryUpdateChecker = Callable[[], Mapping[str, Mapping[str, str]]]
BinaryPresenceChecker = Callable[[], Mapping[str, bool]]


class SettingsUpdateWorker(QThread):
    """Check application and managed-binary updates outside the GUI thread."""

    completed = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(
        self,
        current_app_version: str,
        check_app_updates: AppUpdateChecker | None = None,
        check_binary_updates: BinaryUpdateChecker | None = None,
        check_binary_presence: BinaryPresenceChecker | None = None,
        parent: QObject | None = None,
    ):
        super().__init__(parent)
        self._current_app_version = current_app_version
        self._check_app_updates = check_app_updates
        self._check_binary_updates = check_binary_updates
        self._check_binary_presence = check_binary_presence

    def run(self) -> None:
        """Run all network and filesystem update checks in this worker thread."""
        try:
            check_app_updates = self._check_app_updates
            if check_app_updates is None:
                from utils.app_updater import check_for_updates_strict

                check_app_updates = check_for_updates_strict

            check_binary_updates = self._check_binary_updates
            check_binary_presence = self._check_binary_presence
            if check_binary_updates is None or check_binary_presence is None:
                from utils.bin.manager import (
                    check_binary_presence as default_presence_check,
                    check_updates_available_strict,
                )

                check_binary_updates = (
                    check_binary_updates or check_updates_available_strict
                )
                check_binary_presence = (
                    check_binary_presence or default_presence_check
                )

            summary: UpdateCheckSummary = run_update_check(
                check_app_updates,
                check_binary_updates,
                check_binary_presence,
                self._current_app_version,
            )
        except Exception as exc:
            error_message = redact_urls_in_text(exc) or exc.__class__.__name__
            log.error(
                f"Settings update check failed: {error_message}",
                exc_info=True,
            )
            self.failed.emit(error_message)
            return

        self.completed.emit(summary)
