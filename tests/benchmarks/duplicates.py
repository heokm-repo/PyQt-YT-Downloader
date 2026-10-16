"""M3: real SQLite lookups with independent result and query-count checks."""

from __future__ import annotations

from pathlib import Path
import sqlite3
from unittest.mock import patch

from .fixtures import create_history, expected_duplicates, playlist_ids, task_records
from .measurements import measure


class CountedTasks(list):
    visits = 0

    def __iter__(self):
        for task in super().__iter__():
            self.visits += 1
            yield task


def benchmark_duplicates(output: Path, settings: dict, repeats: int,
                         history_sizes: list[int]) -> list[dict]:
    from core.playlist_filter import filter_duplicate_videos
    from data.managers import HistoryManager
    from data.models import DownloadTask

    results = []
    real_connect = sqlite3.connect
    for history_count in history_sizes:
        db = output / f"history-{history_count}.db"
        create_history(db, history_count)
        manager = HistoryManager()
        manager.db_path = str(db)
        for task_count in (0, 1000):
            records = task_records(task_count, settings)
            tasks = CountedTasks(DownloadTask.from_dict(r) for r in records)
            for playlist_count in (1, 100, 1000):
                ids = playlist_ids(playlist_count)
                expected = expected_duplicates(ids, records, history_count)

                def operation():
                    counts = {"connections": 0, "selects": 0}
                    tasks.visits = 0

                    def trace(sql):
                        if sql.lstrip().upper().startswith("SELECT"):
                            counts["selects"] += 1

                    def connect(*args, **kwargs):
                        counts["connections"] += 1
                        connection = real_connect(*args, **kwargs)
                        connection.set_trace_callback(trace)
                        return connection

                    with patch.object(sqlite3, "connect", connect):
                        actual = filter_duplicate_videos(ids, manager, tasks, "mp4")
                    assert actual == expected, (actual, expected)
                    return {**counts, "task_visits": tasks.visits,
                            "duplicate_count": actual[1], "filtered_ids": actual[0]}

                result = {"history_rows": history_count, "tasks": task_count,
                          "playlist_inputs": playlist_count, **measure(operation, repeats)}
                results.append(result)
                print(f"M3 history={history_count} tasks={task_count} playlist={playlist_count}: "
                      f"{result['elapsed_ms']['median']:.2f} ms", flush=True)
    return results
