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


def build_error_message(template: str, error: Any) -> str:
    """Format an error message template with a normalized exception string."""
    return template.format(error=str(error))
