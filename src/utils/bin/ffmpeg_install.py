"""FFmpeg ZIP install helpers for managed binary downloads."""

import os
from typing import Any, Callable, Mapping
from uuid import uuid4

from utils.bin.archive import extract_zip_member_ending_with
from utils.bin.install import version_record
from utils.logger import log


def _rollback_binary_pair(
    installed_targets: list[str],
    backups: list[tuple[str, str]],
) -> bool:
    """Restore both original binaries after a failed bundle commit."""
    rollback_ok = True
    for target_path in reversed(installed_targets):
        try:
            if os.path.exists(target_path):
                os.remove(target_path)
        except OSError as exc:
            rollback_ok = False
            log.error(
                f"Failed to remove partially installed binary "
                f"{target_path}: {exc}"
            )

    for backup_path, target_path in reversed(backups):
        try:
            if os.path.exists(backup_path):
                os.replace(backup_path, target_path)
        except OSError as exc:
            rollback_ok = False
            log.error(
                f"Failed to restore binary backup "
                f"{backup_path} -> {target_path}: {exc}"
            )
    return rollback_ok


def _remove_install_artifact(path: str, description: str) -> None:
    """Remove a temporary install artifact and report cleanup failures."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        log.warning(f"Failed to clean {description} {path}: {exc}")


def _restore_version_snapshot(
    original_versions: Mapping[str, Any],
    save_versions: Callable[[dict[str, Any]], bool],
) -> bool:
    """Best-effort restore version metadata after a failed bundle commit."""
    try:
        restored = save_versions(dict(original_versions))
    except Exception as exc:
        log.error(
            f"Failed to restore FFmpeg version metadata: {exc}",
            exc_info=True,
        )
        return False
    if not restored:
        log.error("Failed to restore FFmpeg version metadata")
    return restored


def install_ffmpeg_from_zip(
    zip_path: str,
    ffmpeg_path: str,
    ffprobe_path: str,
    version: str,
    ffmpeg_member_suffixes: tuple[str, ...],
    ffprobe_member_suffixes: tuple[str, ...],
    load_versions: Callable[[], Mapping[str, Any]],
    save_versions: Callable[[dict[str, Any]], bool],
) -> bool:
    """Extract ffmpeg and ffprobe and persist their shared version."""
    install_id = uuid4().hex
    temp_ffmpeg = f"{ffmpeg_path}.{install_id}.installing"
    temp_ffprobe = f"{ffprobe_path}.{install_id}.installing"
    backup_ffmpeg = f"{ffmpeg_path}.{install_id}.backup"
    backup_ffprobe = f"{ffprobe_path}.{install_id}.backup"
    installed_targets: list[str] = []
    backups: list[tuple[str, str]] = []
    original_versions: dict[str, Any] = {}
    metadata_commit_attempted = False
    try:
        original_versions = dict(load_versions())
        extracted = extract_zip_member_ending_with(
            zip_path, temp_ffmpeg, ffmpeg_member_suffixes
        )
        if not extracted:
            log.error("ffmpeg.exe not found in zip archive")
            return False

        extracted = extract_zip_member_ending_with(
            zip_path, temp_ffprobe, ffprobe_member_suffixes
        )
        if not extracted:
            log.error("ffprobe.exe not found in zip archive")
            return False

        for staged_path, target_path, backup_path in (
            (temp_ffmpeg, ffmpeg_path, backup_ffmpeg),
            (temp_ffprobe, ffprobe_path, backup_ffprobe),
        ):
            if os.path.exists(target_path):
                os.replace(target_path, backup_path)
                backups.append((backup_path, target_path))
            os.replace(staged_path, target_path)
            installed_targets.append(target_path)

        metadata_commit_attempted = True
        updated_versions = version_record(
            original_versions,
            "ffmpeg",
            version,
        )
        if not save_versions(updated_versions):
            log.error("Failed to persist FFmpeg bundle version; rolling back")
            _rollback_binary_pair(installed_targets, backups)
            _restore_version_snapshot(original_versions, save_versions)
            return False

        for backup_path, _target_path in backups:
            _remove_install_artifact(backup_path, "FFmpeg backup")
        log.info(f"FFmpeg tools extracted to {ffmpeg_path} and {ffprobe_path}")
        return True
    except Exception as exc:
        log.error(f"Failed to commit FFmpeg tool bundle: {exc}", exc_info=True)
        if not _rollback_binary_pair(installed_targets, backups):
            log.error("FFmpeg tool bundle rollback was incomplete")
        if metadata_commit_attempted:
            _restore_version_snapshot(original_versions, save_versions)
        return False
    finally:
        for temp_path in (temp_ffmpeg, temp_ffprobe):
            _remove_install_artifact(
                temp_path,
                "FFmpeg install temporary file",
            )
