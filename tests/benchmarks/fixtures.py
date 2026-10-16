"""Deterministic synthetic inputs. No cookies, real URLs or user data are read."""

from __future__ import annotations

from pathlib import Path
import sqlite3


FIXTURE_VERSION = 1
STATUSES = ("failed", "downloading", "paused", "waiting", "finished")
FORMATS = ("mp4", "mkv", "webm", "mp3", "m4a", "wav")
LIST_SIZES = (10, 100, 1000)
HISTORY_SIZES = (1000, 10000, 100000)


def settings_fixture(downloads: Path) -> dict:
    return {
        "download_folder": str(downloads), "video_quality": "best",
        "audio_quality": "best", "format": "mp4", "max_downloads": 3,
        "normalize_audio": False, "use_acceleration": False,
        "universal_compatibility": False, "language": "ko", "theme": "light",
        "window_states": {}, "benchmark_unknown_key": {"preserve": "한글 ✓"},
    }


def task_records(count: int, settings: dict) -> list[dict]:
    return [
        {
            "id": i + 1, "url": f"https://example.invalid/video/{i:010d}",
            "status": STATUSES[i % len(STATUSES)], "video_id": f"v{i:010d}",
            "extractor": "youtube", "output_path": "",
            "settings": {**settings, "format": FORMATS[i % len(FORMATS)]},
            "meta": {"title": f"기준 영상 {i + 1:04d} — UTF-8 ✓",
                     "uploader": "Synthetic fixture", "duration": 125},
            "workspace_id": f"{i + 1:032x}", "legacy_workspace": False,
        }
        for i in range(count)
    ]


def expected_order(records: list[dict], mode: str) -> list[int]:
    """Independent oracle, intentionally not using production sort constants."""
    if mode == "status":
        ordered = sorted(records, key=lambda r: (STATUSES.index(r["status"]), -r["id"]))
    else:
        ordered = sorted(records, key=lambda r: r["id"], reverse=mode == "newest")
    return [record["id"] for record in ordered]


def history_rows(count: int):
    for i in range(count):
        yield ("youtube", f"v{i * 2:010d}", "mp4", f"기준 이력 {i}",
               "Synthetic fixture", "2026-10-13 00:00:00")


def create_history(path: Path, count: int, *, legacy: bool = False) -> None:
    """Use the existing on-disk schema, independently of HistoryManager."""
    connection = sqlite3.connect(path)
    try:
        if legacy:
            connection.execute(
                "CREATE TABLE downloads (video_id TEXT, format TEXT, title TEXT, "
                "uploader TEXT, download_date TEXT, PRIMARY KEY (video_id, format))"
            )
            connection.executemany("INSERT INTO downloads VALUES (?, ?, ?, ?, ?)",
                                   (row[1:] for row in history_rows(count)))
        else:
            connection.execute(
                "CREATE TABLE downloads (extractor TEXT, video_id TEXT, format TEXT, "
                "title TEXT, uploader TEXT, download_date TEXT, "
                "PRIMARY KEY (extractor, video_id, format))"
            )
            connection.executemany("INSERT INTO downloads VALUES (?, ?, ?, ?, ?, ?)",
                                   history_rows(count))
        connection.commit()
    finally:
        connection.close()


def playlist_ids(count: int) -> list[str]:
    # Every fifth input repeats a non-history ID. Preserve those repetitions.
    return [f"v{(1 if i % 5 == 4 else i):010d}" for i in range(count)]


def expected_duplicates(ids: list[str], records: list[dict], history_count: int,
                        target_format: str = "mp4", extractor: str = "youtube"):
    history = {(e, vid, fmt) for e, vid, fmt, *_ in history_rows(history_count)}
    active = {(r["extractor"], r["video_id"], r["settings"].get("format", "mp4"))
              for r in records if r["status"] in ("waiting", "downloading", "paused")}
    known = history | active
    filtered = [vid for vid in ids if (extractor, vid, target_format) not in known]
    return filtered, len(ids) - len(filtered)
