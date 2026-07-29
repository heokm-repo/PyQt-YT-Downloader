"""Minimal filesystem state for resuming a task after yt-dlp has succeeded."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from utils.logger import log


READY_MARKER_FILENAME = ".source_ready.json"


@dataclass(frozen=True)
class ReadySource:
    source_path: str
    final_name: str
    audio_bitrate: int | None = None
    destination_size_before: int | None = None
    destination_mtime_before: int | None = None


def _path_inside_workspace(path: Path, workspace: Path) -> bool:
    try:
        path.resolve(strict=True).relative_to(workspace.resolve(strict=True))
        return path.is_file()
    except (OSError, RuntimeError, ValueError):
        return False


def _path_location_inside_workspace(path: Path, workspace: Path) -> bool:
    try:
        path.resolve().relative_to(workspace.resolve())
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def ready_marker_path(workspace: str) -> Path:
    return Path(workspace, READY_MARKER_FILENAME)


def write_ready_source(
    workspace: str,
    source_path: str,
    final_name: str,
    audio_bitrate: object = None,
    destination_path: str | None = None,
) -> ReadySource:
    """Atomically mark a verified yt-dlp output as ready for finalization."""
    workspace_path = Path(workspace)
    source = Path(source_path)
    if not _path_inside_workspace(source, workspace_path):
        raise ValueError("Ready source is outside the task workspace")

    relative_source = source.resolve(strict=True).relative_to(
        workspace_path.resolve(strict=True)
    )
    normalized_bitrate = None
    try:
        parsed_bitrate = int(audio_bitrate)
        if parsed_bitrate > 0:
            normalized_bitrate = parsed_bitrate
    except (TypeError, ValueError):
        normalized_bitrate = None

    destination_size_before = None
    destination_mtime_before = None
    if destination_path:
        try:
            destination_stat = os.stat(destination_path)
            destination_size_before = destination_stat.st_size
            destination_mtime_before = destination_stat.st_mtime_ns
        except OSError:
            destination_size_before = None
            destination_mtime_before = None

    payload = {
        "source": str(relative_source),
        "final_name": Path(final_name).name,
        "audio_bitrate": normalized_bitrate,
        "destination_size_before": destination_size_before,
        "destination_mtime_before": destination_mtime_before,
    }
    marker = ready_marker_path(workspace)
    temporary = marker.with_name(f"{marker.name}.{uuid4().hex}.tmp")
    try:
        with open(temporary, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, marker)
    finally:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError as exc:
                log.debug(
                    "Failed to remove temporary ready marker %s: %s",
                    temporary,
                    exc,
                )

    return ReadySource(
        str(source.resolve()),
        payload["final_name"],
        normalized_bitrate,
        destination_size_before,
        destination_mtime_before,
    )


def read_ready_source(workspace: str) -> ReadySource | None:
    """Return a valid ready source, ignoring corrupt or stale marker data."""
    marker = ready_marker_path(workspace)
    try:
        with open(marker, "r", encoding="utf-8") as stream:
            payload: Mapping[str, Any] = json.load(stream)
        relative_source = str(payload.get("source") or "").strip()
        final_name = Path(str(payload.get("final_name") or "")).name
        if not relative_source or not final_name:
            return None
        source = Path(workspace, relative_source)
        if not _path_location_inside_workspace(source, Path(workspace)):
            return None
        audio_bitrate = payload.get("audio_bitrate")
        normalized_bitrate = int(audio_bitrate) if audio_bitrate else None
        size_before = payload.get("destination_size_before")
        mtime_before = payload.get("destination_mtime_before")
        return ReadySource(
            str(source.resolve()),
            final_name,
            normalized_bitrate,
            int(size_before) if size_before is not None else None,
            int(mtime_before) if mtime_before is not None else None,
        )
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


def remove_ready_marker(workspace: str) -> None:
    try:
        ready_marker_path(workspace).unlink()
    except FileNotFoundError:
        return
    except OSError as exc:
        log.warning(
            "Failed to remove ready marker from %s: %s",
            workspace,
            exc,
        )


def destination_changed_since_ready(
    ready_source: ReadySource,
    destination_path: str,
) -> bool:
    """Return whether a final file is new or changed since yt-dlp completed."""
    try:
        current = os.stat(destination_path)
    except OSError:
        return False
    if (
        ready_source.destination_size_before is None
        or ready_source.destination_mtime_before is None
    ):
        return True
    return (
        current.st_size != ready_source.destination_size_before
        or current.st_mtime_ns != ready_source.destination_mtime_before
    )
