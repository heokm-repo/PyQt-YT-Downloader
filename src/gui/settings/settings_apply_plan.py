"""Build the actions needed after settings are accepted."""

from dataclasses import dataclass
from typing import Any, Mapping

from constants import KEY_LANGUAGE
from core.scheduler_settings import should_adjust_worker_count, target_worker_count
from locales import DEFAULT_LANGUAGE


@dataclass(frozen=True)
class SettingsApplyPlan:
    language: str
    adjust_worker_count: bool
    worker_count: int


def build_settings_apply_plan(
    old_settings: Mapping[str, Any], new_settings: Mapping[str, Any]
) -> SettingsApplyPlan:
    """Return the language and scheduler changes implied by accepted settings."""
    return SettingsApplyPlan(
        language=new_settings.get(KEY_LANGUAGE, DEFAULT_LANGUAGE),
        adjust_worker_count=should_adjust_worker_count(old_settings, new_settings),
        worker_count=target_worker_count(new_settings),
    )