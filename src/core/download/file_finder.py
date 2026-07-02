"""Locate completed download files."""

import re
from pathlib import Path
from typing import Any, Mapping, Optional

from constants import MEDIA_EXTENSIONS
from utils.logger import log

_TITLE_CHARS_RE = re.compile(r"[^\w가-힣]")


def clean_title_for_match(title: str) -> str:
    """Normalize a media title for loose filename comparison."""
    return _TITLE_CHARS_RE.sub("", title or "").lower()


def find_downloaded_file(
    current_output_path: str,
    metadata: Mapping[str, Any],
    save_path: str,
    task_id: Optional[int] = None,
) -> str:
    """Return the best matching completed media file path, or an empty string."""
    if current_output_path:
        try:
            captured_path = Path(current_output_path).resolve()
            if captured_path.exists():
                return str(captured_path)
        except (OSError, RuntimeError) as exc:
            log.debug(f"Captured output path is not usable (task_id={task_id}, path={current_output_path}): {exc}")

    save_dir = Path(save_path)
    if not save_dir.exists():
        return ""

    try:
        clean_title = clean_title_for_match(str(metadata.get("title", "")))
        if not clean_title:
            return ""

        for file_path in save_dir.iterdir():
            if not file_path.is_file():
                continue

            clean_stem = clean_title_for_match(file_path.stem)
            if clean_title in clean_stem and file_path.suffix.lower() in MEDIA_EXTENSIONS:
                return str(file_path.resolve())
    except Exception as exc:
        if task_id is None:
            log.warning(f"파일 경로 찾기 실패: {exc}")
        else:
            log.warning(f"파일 경로 찾기 실패 (task_id={task_id}): {exc}")

    return ""
