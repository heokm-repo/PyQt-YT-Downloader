"""Build scheduler payloads for resuming paused tasks."""

from dataclasses import dataclass
from typing import Any, Mapping, Optional


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
    meta = getattr(task, "meta", None)
    if not url or not meta:
        return None

    settings = getattr(task, "settings", None) or dict(default_settings)
    return ResumeTaskPlan(url=url, settings=settings, meta=meta)