"""Button specs shown by task widgets for each task status."""

from dataclasses import dataclass
from typing import Any

from constants import TaskStatus
from locales.strings import STR
from resources.styles import (
    COLOR_BTN_BLUE,
    COLOR_BTN_GRAY,
    COLOR_BTN_GREEN,
    COLOR_BTN_ORANGE,
    COLOR_BTN_RED,
)


@dataclass(frozen=True)
class TaskButtonSpec:
    action: str
    icon_name: str
    tooltip: str
    color: str


def _remove_button() -> TaskButtonSpec:
    return TaskButtonSpec(
        "remove", "mdi.close", STR.TOOLTIP_REMOVE, COLOR_BTN_GRAY
    )


def get_task_button_specs(status: Any) -> list[TaskButtonSpec]:
    """Return button specs for a task widget status."""
    remove_button = _remove_button()
    button_specs = {
        TaskStatus.DOWNLOADING: [
            TaskButtonSpec(
                "pause", "mdi.pause", STR.TOOLTIP_PAUSE, COLOR_BTN_RED
            ),
            TaskButtonSpec(
                "delete_file", "mdi.delete", STR.TOOLTIP_CANCEL, COLOR_BTN_RED
            ),
        ],
        TaskStatus.PAUSED: [
            TaskButtonSpec(
                "resume", "mdi.play", STR.TOOLTIP_RESUME, COLOR_BTN_GREEN
            ),
            remove_button,
        ],
        TaskStatus.FINISHED: [
            TaskButtonSpec(
                "play", "mdi.play", STR.TOOLTIP_PLAY, COLOR_BTN_GREEN
            ),
            TaskButtonSpec(
                "open_folder",
                "mdi.folder-open",
                STR.TOOLTIP_OPEN_FOLDER,
                COLOR_BTN_BLUE,
            ),
            TaskButtonSpec(
                "delete_file", "mdi.delete", STR.TOOLTIP_DELETE_FILE, COLOR_BTN_RED
            ),
            remove_button,
        ],
        TaskStatus.FAILED: [
            TaskButtonSpec(
                "retry", "mdi.refresh", STR.TOOLTIP_RETRY, COLOR_BTN_ORANGE
            ),
            remove_button,
        ],
    }
    return button_specs.get(status, [remove_button])