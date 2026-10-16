"""Isolated benchmark directories and reproducibility metadata."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def prepare_run(output: Path, *, qt_platform: str = "offscreen") -> Path:
    """Refuse reuse: each run owns fresh AppData, downloads, temp and results."""
    output = output.resolve()
    output.relative_to(ROOT / "build" / "benchmarks")
    output.mkdir(parents=True, exist_ok=False)
    for name in ("appdata", "localappdata", "downloads", "temp"):
        (output / name).mkdir()
    os.environ.update(
        APPDATA=str(output / "appdata"),
        LOCALAPPDATA=str(output / "localappdata"),
        TEMP=str(output / "temp"),
        TMP=str(output / "temp"),
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUTF8="1",
        QT_QPA_PLATFORM=qt_platform,
        QT_SCALE_FACTOR="1",
    )
    # Must precede all application imports, including logger initialization.
    sys.path.insert(0, str(ROOT / "src"))
    return output


def file_manifest(root: Path, *, suffixes: set[str] | None = None) -> list[dict]:
    records = []
    for path in sorted(root.rglob("*")):
        if (path.is_file() and "__pycache__" not in path.parts
                and (suffixes is None or path.suffix in suffixes)):
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            records.append({"path": path.relative_to(root).as_posix(),
                            "bytes": path.stat().st_size, "sha256": digest})
    return records


def environment_manifest() -> dict:
    def git(*args):
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, encoding="utf-8"
        ).strip()

    return {
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "commit": git("rev-parse", "HEAD"),
        "working_tree": git("status", "--porcelain=v1"),
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpu_count": os.cpu_count(),
        "packages": dict(sorted((d.metadata["Name"], d.version)
                                for d in importlib.metadata.distributions()
                                if d.metadata.get("Name"))),
        "qt_platform": os.environ.get("QT_QPA_PLATFORM"),
        "qt_scale_factor": os.environ.get("QT_SCALE_FACTOR"),
        "power_plan": "not controlled; record externally for cross-session comparisons",
        "source_files": file_manifest(ROOT / "src", suffixes={".py"}),
    }
