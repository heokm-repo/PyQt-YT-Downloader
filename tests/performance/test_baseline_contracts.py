"""Fast behavior contracts for the offline benchmark fixtures; no timing gates."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from unittest.mock import patch

import pytest

from constants import TaskStatus
from core.playlist_filter import filter_duplicate_videos
from data.managers import HistoryManager, TaskManager
from data.models import DownloadTask
from gui.windows.main_window import YTDownloaderPyQt5
from tests.benchmarks.fixtures import (
    create_history, expected_duplicates, expected_order, playlist_ids, settings_fixture, task_records,
)
from tests.benchmarks.measurements import distribution


@pytest.mark.parametrize("legacy", [False, True])
def test_fixture_history_keeps_format_extractor_and_repeated_input_semantics(tmp_path, legacy):
    create_history(tmp_path / "history.db", 1000, legacy=legacy)
    records = task_records(1000, settings_fixture(tmp_path))
    tasks = [DownloadTask.from_dict(r) for r in records]
    ids = playlist_ids(1000)
    with patch("data.history_store.get_user_data_path", return_value=str(tmp_path)):
        history = HistoryManager()
    for extractor, fmt in (("youtube", "mp4"), ("youtube", "mp3"), ("vimeo", "mp4")):
        assert filter_duplicate_videos(ids, history, tasks, fmt, extractor) == expected_duplicates(
            ids, records, 1000, fmt, extractor
        )
    assert history.is_downloaded("youtube", "v0000000000", "mp4")
    assert not history.is_downloaded("youtube", "v0000000000", "mp3")
    assert not history.is_downloaded("vimeo", "v0000000000", "mp4")
    history.add_to_history("vimeo", "v0000000000", {"title": "한글 ✓"}, "mp3")
    assert history.is_downloaded("vimeo", "v0000000000", "mp3")
    history.remove_from_history("vimeo", "v0000000000", "mp3")
    assert not history.is_downloaded("vimeo", "v0000000000", "mp3")
    connection = sqlite3.connect(tmp_path / "history.db")
    try:
        assert connection.execute("SELECT COUNT(*) FROM downloads").fetchone()[0] == 1000
    finally:
        connection.close()


def test_task_fixture_round_trip_normalizes_only_active_status_and_preserves_utf8(tmp_path):
    records = task_records(10, settings_fixture(tmp_path))
    tasks = [DownloadTask.from_dict(r) for r in records]
    with patch("data.managers.get_user_data_path", return_value=str(tmp_path)):
        manager = TaskManager()
    manager.save_tasks(tasks)
    saved = manager.load_tasks()
    expected = [{**record, "status": "paused" if record["status"] in ("waiting", "downloading")
                 else record["status"]} for record in records]
    assert saved == expected
    assert [task.to_dict() for task in tasks] == records
    assert "기준 영상" in Path(manager.tasks_file).read_text(encoding="utf-8")
    assert json.loads(Path(manager.tasks_file).read_text(encoding="utf-8")) == expected


def test_settings_fixture_round_trip_preserves_unknown_keys_and_window_states(tmp_path):
    from utils import settings_store

    settings = settings_fixture(tmp_path / "downloads")
    settings["window_states"] = {
        "MainWindow": {"x": -1200, "y": 40, "width": 1200, "height": 800, "maximized": True},
        "Secondary": {"x": 30, "y": 40, "width": 600, "height": 400, "maximized": False},
    }
    with patch.object(settings_store, "get_user_data_path", return_value=str(tmp_path)):
        settings_store.save_settings(settings)
        loaded = settings_store.load_settings()
        assert loaded == settings
        loaded["theme"] = "dark"
        settings_store.save_settings(loaded)
        saved = json.loads((tmp_path / "settings.json").read_text(encoding="utf-8"))
    assert saved["window_states"] == settings["window_states"]
    assert saved["benchmark_unknown_key"] == {"preserve": "한글 ✓"}
    assert saved["theme"] == "dark"


@pytest.mark.parametrize("mode", ["newest", "oldest", "status"])
def test_fixture_sort_order_keeps_source_order_and_status_ties(tmp_path, mode):
    from types import SimpleNamespace

    records = task_records(1000, settings_fixture(tmp_path))
    tasks = [DownloadTask.from_dict(r) for r in records]
    window = SimpleNamespace(tasks=tasks, task_widgets={t.id: object() for t in tasks},
                             _current_task_sort_key=lambda: mode)
    assert YTDownloaderPyQt5._sorted_task_ids(window) == expected_order(records, mode)
    assert [t.id for t in tasks] == list(range(1, 1001))
    assert {t.status for t in tasks} == set(TaskStatus)


def test_distribution_uses_nearest_rank_p95_and_keeps_raw_order():
    values = list(range(20, 0, -1))
    result = distribution(values)
    assert result["samples"] == values
    assert (result["median"], result["p95"], result["min"], result["max"]) == (10.5, 19, 1, 20)
