"""Small app-management helpers for the settings dialog."""

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class UninstallAvailability:
    can_uninstall: bool
    message: str | None = None


@dataclass(frozen=True)
class UninstallCompletionResult:
    should_quit: bool
    error_message: str | None = None


@dataclass(frozen=True)
class UninstallFlowResult:
    availability: UninstallAvailability | None = None
    completion: UninstallCompletionResult | None = None
    cancelled: bool = False

    @property
    def should_quit(self) -> bool:
        return bool(self.completion and self.completion.should_quit)

    @property
    def error_message(self) -> str | None:
        if not self.completion:
            return None
        return self.completion.error_message

    @property
    def development_message(self) -> str | None:
        if self.availability and not self.availability.can_uninstall:
            return self.availability.message
        return None


@dataclass(frozen=True)
class UpdateCheckResult:
    update_available: bool
    latest_version: str
    download_url: str
    message: str
    expected_digest: str | None = None


@dataclass(frozen=True)
class UpdateCompletionResult:
    should_quit: bool
    error_message: str | None = None


@dataclass(frozen=True)
class UpdateFlowResult:
    check_result: UpdateCheckResult
    completion: UpdateCompletionResult | None = None
    cancelled: bool = False

    @property
    def update_available(self) -> bool:
        return self.check_result.update_available

    @property
    def should_quit(self) -> bool:
        return bool(self.completion and self.completion.should_quit)

    @property
    def error_message(self) -> str | None:
        if not self.completion:
            return None
        return self.completion.error_message


def is_development_environment(is_frozen: bool) -> bool:
    """Return True when the app is running outside a packaged executable."""
    return not is_frozen


def build_uninstall_availability(
    is_frozen: bool, development_message: str
) -> UninstallAvailability:
    """Return whether the app can run its packaged uninstaller."""
    if is_development_environment(is_frozen):
        return UninstallAvailability(False, development_message)
    return UninstallAvailability(True)


def build_uninstall_completion_result(
    uninstall_started: bool, start_error_message: str
) -> UninstallCompletionResult:
    """Return the result shown after trying to start the uninstaller."""
    if uninstall_started:
        return UninstallCompletionResult(True)
    return UninstallCompletionResult(False, start_error_message)


def run_uninstall_flow(
    confirm_uninstall: Callable[[], bool],
    is_frozen: bool,
    uninstall_app: Callable[[], bool],
    development_message: str,
    start_error_message: str,
) -> UninstallFlowResult:
    """Run the non-UI uninstall flow with injected side-effect functions."""
    if not confirm_uninstall():
        return UninstallFlowResult(cancelled=True)

    availability = build_uninstall_availability(is_frozen, development_message)
    if not availability.can_uninstall:
        return UninstallFlowResult(availability=availability)

    completion = build_uninstall_completion_result(
        uninstall_app(),
        start_error_message,
    )
    return UninstallFlowResult(availability=availability, completion=completion)


def build_update_available_message(
    template: str, current_version: str, latest_version: str
) -> str:
    """Format the update prompt shown when a new version is available."""
    return template.format(current=current_version, latest=latest_version)


def build_error_message(template: str, error: Any) -> str:
    """Format an error message template with a normalized exception string."""
    return template.format(error=str(error))


def build_update_check_result(
    update_available: bool,
    latest_version: str,
    download_url: str,
    current_version: str,
    latest_message: str,
    available_template: str,
    expected_digest: str | None = None,
) -> UpdateCheckResult:
    """Build the message and data needed after checking for updates."""
    if update_available:
        message = build_update_available_message(
            available_template, current_version, latest_version
        )
    else:
        message = latest_message

    return UpdateCheckResult(
        update_available=update_available,
        latest_version=latest_version,
        download_url=download_url,
        message=message,
        expected_digest=expected_digest,
    )


def build_update_completion_result(
    new_exe_path: str | None,
    apply_succeeded: bool,
    download_error_message: str,
    apply_error_message: str,
) -> UpdateCompletionResult:
    """Build the result shown after downloading and applying an update."""
    if not new_exe_path:
        return UpdateCompletionResult(False, download_error_message)
    if not apply_succeeded:
        return UpdateCompletionResult(False, apply_error_message)
    return UpdateCompletionResult(True)


def run_update_flow(
    check_for_updates: Callable[[], tuple[bool, str, str, str | None]],
    download_update: Callable[[str, str | None], str | None],
    apply_update: Callable[[str, str | None], bool],
    confirm_update: Callable[[UpdateCheckResult], bool],
    current_version: str,
    latest_message: str,
    available_template: str,
    download_error_message: str,
    apply_error_message: str,
) -> UpdateFlowResult:
    """Run the non-UI update flow with injected side-effect functions."""
    update_available, latest_version, download_url, expected_digest = check_for_updates()
    check_result = build_update_check_result(
        update_available,
        latest_version,
        download_url,
        current_version,
        latest_message,
        available_template,
        expected_digest,
    )

    if not check_result.update_available:
        return UpdateFlowResult(check_result)

    if not confirm_update(check_result):
        return UpdateFlowResult(check_result, cancelled=True)

    new_exe_path = download_update(
        check_result.download_url,
        check_result.expected_digest,
    )
    apply_succeeded = bool(new_exe_path) and apply_update(
        new_exe_path,
        check_result.expected_digest,
    )
    completion = build_update_completion_result(
        new_exe_path,
        apply_succeeded,
        download_error_message,
        apply_error_message,
    )
    return UpdateFlowResult(check_result, completion=completion)
