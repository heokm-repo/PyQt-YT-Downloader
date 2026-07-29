"""Build scheduler payloads for resuming paused tasks."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional

from gui.tasks.task_workspace_payload import build_workspace_execution_settings


@dataclass(frozen=True)
class ResumeTaskPlan:
    url: str
    settings: Mapping[str, Any]
    meta: Mapping[str, Any]


def build_resume_task_plan(
    task: Any, default_settings: Mapping[str, Any]
) -> Optional[ResumeTaskPlan]:
    """Return scheduler inputs for a resumable task, or None if data is incomplete."""
    url = getattr(task, "url", "")
    if not url:
        return None
    meta = dict(getattr(task, "meta", None) or {})

    settings = build_workspace_execution_settings(
        task,
        getattr(task, "settings", None) or default_settings,
        resume=True,
    )
    output_path = getattr(task, "output_path", "")
    if output_path:
        settings["_resume_output_path"] = output_path
    return ResumeTaskPlan(url=url, settings=settings, meta=meta)
