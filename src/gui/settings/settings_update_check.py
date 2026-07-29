"""Policy helpers for settings-triggered update checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping


APP_COMPONENT = "app"
COMPONENT_ORDER = (APP_COMPONENT, "yt-dlp", "ffmpeg", "ffprobe", "quickjs")
COMPONENT_NAMES = {
    APP_COMPONENT: "YT Downloader",
    "yt-dlp": "yt-dlp",
    "ffmpeg": "FFmpeg",
    "ffprobe": "ffprobe",
    "quickjs": "QuickJS",
}


@dataclass(frozen=True)
class ComponentUpdate:
    """One component that needs an update, installation, or repair."""

    key: str
    name: str
    current: str | None = None
    latest: str | None = None
    missing: bool = False


@dataclass(frozen=True)
class UpdateCheckSummary:
    """Combined app and required-component update check result."""

    updates: tuple[ComponentUpdate, ...] = ()

    @property
    def update_available(self) -> bool:
        return bool(self.updates)


def _binary_update_info(
    component_key: str,
    binary_updates: Mapping[str, Mapping[str, str]],
) -> Mapping[str, str] | None:
    """Return the shared FFmpeg update for ffprobe when applicable."""
    update_key = "ffmpeg" if component_key == "ffprobe" else component_key
    return binary_updates.get(update_key)


def build_update_check_summary(
    app_update_info: tuple[bool, str | None, str | None, str | None],
    binary_updates: Mapping[str, Mapping[str, str]],
    binary_presence: Mapping[str, bool],
    current_app_version: str,
) -> UpdateCheckSummary:
    """Combine app, binary version, and binary presence checks."""
    updates: list[ComponentUpdate] = []
    app_available, latest_app_version, _, _ = app_update_info
    if app_available:
        updates.append(
            ComponentUpdate(
                APP_COMPONENT,
                COMPONENT_NAMES[APP_COMPONENT],
                current_app_version,
                latest_app_version,
            )
        )

    for component_key in COMPONENT_ORDER[1:]:
        update_info = _binary_update_info(component_key, binary_updates)
        missing = not binary_presence.get(component_key, False)
        if not update_info and not missing:
            continue

        updates.append(
            ComponentUpdate(
                component_key,
                COMPONENT_NAMES[component_key],
                update_info.get("current") if update_info else None,
                update_info.get("latest") if update_info else None,
                missing=missing,
            )
        )

    return UpdateCheckSummary(tuple(updates))


def run_update_check(
    check_app_updates: Callable[
        [], tuple[bool, str | None, str | None, str | None]
    ],
    check_binary_updates: Callable[[], Mapping[str, Mapping[str, str]]],
    check_binary_presence: Callable[[], Mapping[str, bool]],
    current_app_version: str,
) -> UpdateCheckSummary:
    """Check every managed update source without applying any update."""
    binary_presence = check_binary_presence()
    binary_updates = check_binary_updates()
    app_update_info = check_app_updates()
    return build_update_check_summary(
        app_update_info,
        binary_updates,
        binary_presence,
        current_app_version,
    )


def format_update_check_message(
    summary: UpdateCheckSummary,
    header: str,
    missing_template: str,
    restart_required: str,
    active_tasks_notice: str,
    has_active_tasks: bool,
) -> str:
    """Build the restart prompt shown after updates are found."""
    lines = [header.rstrip(), ""]
    for update in summary.updates:
        if update.missing:
            lines.append(missing_template.format(name=update.name))
        else:
            lines.append(
                f"\u2022 {update.name}: {update.current or '?'} "
                f"\u2192 {update.latest or '?'}"
            )

    lines.extend(("", restart_required.strip()))
    if has_active_tasks:
        lines.extend(("", active_tasks_notice.strip()))
    return "\n".join(lines)
