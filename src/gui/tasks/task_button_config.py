"""Button specs shown by task widgets for each task status."""

from dataclasses import dataclass
from typing import Any

from constants import TaskStatus
from locales.strings import STR
from resources import colors


@dataclass(frozen=True)
class TaskButtonSpec:
    action: str
    icon_name: str
    tooltip: str
    color: str


def _remove_button() -> TaskButtonSpec:
    return TaskButtonSpec(
        "remove", "mdi.close", STR.TOOLTIP_REMOVE, colors.COLOR_ICON_MUTED
    )


def get_task_button_specs(status: Any) -> list[TaskButtonSpec]:
    """Return button specs for a task widget status."""
    remove_button = _remove_button()
    button_specs = {
        TaskStatus.DOWNLOADING: [
            TaskButtonSpec(
                "pause", "mdi.pause", STR.TOOLTIP_PAUSE, colors.COLOR_ERROR
            ),
            TaskButtonSpec(
                "delete_file", "mdi.delete", STR.TOOLTIP_CANCEL, colors.COLOR_ERROR
            ),
        ],
        TaskStatus.PAUSED: [
            TaskButtonSpec(
                "resume", "mdi.play", STR.TOOLTIP_RESUME, colors.COLOR_SUCCESS
            ),
            remove_button,
        ],
        TaskStatus.FINISHED: [
            TaskButtonSpec(
                "play", "mdi.play", STR.TOOLTIP_PLAY, colors.COLOR_SUCCESS
            ),
            TaskButtonSpec(
                "open_folder",
                "mdi.folder-open",
                STR.TOOLTIP_OPEN_FOLDER,
                colors.COLOR_INFO,
            ),
            TaskButtonSpec(
                "delete_file", "mdi.delete", STR.TOOLTIP_DELETE_FILE, colors.COLOR_ERROR
            ),
            remove_button,
        ],
        TaskStatus.FAILED: [
            TaskButtonSpec(
                "retry", "mdi.refresh", STR.TOOLTIP_RETRY, colors.COLOR_WARNING
            ),
            remove_button,
        ],
    }
    return button_specs.get(status, [remove_button])
