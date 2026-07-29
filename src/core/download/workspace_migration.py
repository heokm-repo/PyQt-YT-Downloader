"""Migration of deterministic legacy temp directories to task UUIDs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from constants import DEFAULT_FORMAT
from core.download.temp_workspace import task_temp_path, task_workspace_path
from utils.logger import log


@dataclass(frozen=True)
class WorkspacePreparation:
    """Result of preparing one task's current workspace."""

    workspace_path: str
    migrated_from: str | None = None


class WorkspaceMigrationError(OSError):
    """Raised when a legacy workspace exists but cannot be migrated safely."""


def legacy_workspace_paths(
    save_path: str,
    identity: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """
    Return every legacy path a persisted task may have used.

    Older non-YouTube tasks could start under ``unknown + URL`` and later
    resume under their fetched ``extractor + media ID`` identity. A known
    extractor with no initial media ID used ``extractor + URL``.
    """
    descriptor = identity or {}
    extractor = descriptor.get("extractor") or "unknown"
    video_id = descriptor.get("video_id")
    url = descriptor.get("url")
    output_format = descriptor.get("format") or DEFAULT_FORMAT

    identity_pairs: list[tuple[object, object]] = []
    if video_id:
        identity_pairs.append((extractor, video_id))
    if url:
        identity_pairs.append((extractor, url))
        identity_pairs.append(("unknown", url))

    paths: list[str] = []
    for candidate_extractor, candidate_id in identity_pairs:
        candidate = task_temp_path(
            save_path,
            candidate_extractor,
            candidate_id,
            output_format,
        )
        if candidate not in paths:
            paths.append(candidate)
    return tuple(paths)


def prepare_task_workspace(
    save_path: str,
    workspace_id: str,
    *,
    migrate_legacy: bool = False,
    legacy_identity: Mapping[str, Any] | None = None,
) -> WorkspacePreparation:
    """Create a UUID workspace, moving one matching legacy directory first."""
    target = Path(task_workspace_path(save_path, workspace_id))
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.is_symlink():
        raise WorkspaceMigrationError(
            f"Task workspace cannot be a symbolic link: {target}"
        )
    if target.exists() and not target.is_dir():
        raise WorkspaceMigrationError(
            f"Task workspace is not a directory: {target}"
        )

    legacy_paths = (
        legacy_workspace_paths(save_path, legacy_identity)
        if migrate_legacy
        else ()
    )
    available_sources = tuple(
        Path(path)
        for path in legacy_paths
        if Path(path).is_dir() and not Path(path).is_symlink()
    )

    if target.exists() and available_sources:
        try:
            target_has_content = next(target.iterdir(), None) is not None
        except OSError as exc:
            raise WorkspaceMigrationError(
                f"Could not inspect task workspace {target}: {exc}"
            ) from exc
        if target_has_content:
            # A non-empty current workspace always takes precedence.
            return WorkspacePreparation(str(target))
        try:
            target.rmdir()
        except OSError as exc:
            raise WorkspaceMigrationError(
                f"Could not replace empty task workspace {target}: {exc}"
            ) from exc

    if target.exists() or not migrate_legacy:
        target.mkdir(parents=True, exist_ok=True)
        return WorkspacePreparation(str(target))

    migration_errors: list[OSError] = []
    for source in available_sources:
        try:
            source.rename(target)
            log.info(
                "Migrated legacy task workspace %s to %s",
                source,
                target,
            )
            return WorkspacePreparation(str(target), str(source))
        except FileExistsError:
            return WorkspacePreparation(str(target))
        except OSError as exc:
            migration_errors.append(exc)
            log.warning(
                "Failed to migrate legacy task workspace %s to %s: %s",
                source,
                target,
                exc,
            )

    if available_sources:
        detail = migration_errors[-1] if migration_errors else "unknown error"
        raise WorkspaceMigrationError(
            f"Could not migrate legacy task workspace to {target}: {detail}"
        )

    target.mkdir(parents=True, exist_ok=True)
    return WorkspacePreparation(str(target))
