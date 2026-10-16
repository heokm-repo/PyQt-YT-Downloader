"""Exercise actual SQLite migrations, variable limits and connection closure."""
from contextlib import closing
import math
import sqlite3
from unittest.mock import patch

import pytest

from data.history_store import HistoryManager, HISTORY_QUERY_BATCH_SIZE


class TrackedConnection(sqlite3.Connection):
    closed = False

    def close(self):
        self.closed = True
        super().close()


@pytest.fixture
def tracked_connections(monkeypatch):
    real_connect = sqlite3.connect
    connections, queries = [], []

    def connect(*args, **kwargs):
        conn = real_connect(*args, **kwargs, factory=TrackedConnection)
        conn.set_trace_callback(queries.append)
        connections.append(conn)
        return conn

    monkeypatch.setattr(sqlite3, 'connect', connect)
    return connections, queries


@pytest.mark.parametrize('limit', [32, 999])
def test_batch_lookup_uses_one_closed_connection_and_bounded_queries(tmp_path, tracked_connections, limit):
    connections, queries = tracked_connections
    store = HistoryManager(tmp_path / 'history.db')
    ids = [f'Case-{i}' for i in range(2005)]
    with closing(sqlite3.connect(store.db_path)) as conn, conn:
        conn.executemany('INSERT INTO downloads VALUES (?, ?, ?, ?, ?, ?)',
                         [('Example', video_id, 'mp4', '한글', '', '') for video_id in ids])
    connect = sqlite3.connect

    def limited(*args, **kwargs):
        conn = connect(*args, **kwargs)
        conn.setlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER, limit)
        return conn

    connections.clear()
    queries.clear()
    with patch.object(sqlite3, 'connect', side_effect=limited):
        actual = store.find_downloaded_ids('Example', ids + ids[:10] + ['missing'], 'mp4')
    assert actual == set(ids)
    assert len(connections) == 1 and connections[0].closed
    selects = [query for query in queries if query.startswith('SELECT')]
    assert len(selects) == math.ceil((len(ids) + 1) / min(HISTORY_QUERY_BATCH_SIZE, limit - 2))
    with pytest.raises(sqlite3.ProgrammingError):
        connections[0].execute('SELECT 1')


def test_crud_preserves_case_format_and_extractor_and_closes_connections(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    store = HistoryManager(tmp_path / 'history.db')
    video_id = "a' OR 1=1 --"
    store.add_to_history('Example', video_id, {'title': '한글 ✓'}, 'webm')
    store.add_to_history('Example', video_id, {'title': '새 제목'}, 'webm')
    assert store.is_downloaded('Example', video_id, 'webm')
    assert not store.is_downloaded('example', video_id, 'webm')
    assert not store.is_downloaded('Example', video_id, 'mp4')
    with closing(sqlite3.connect(store.db_path)) as conn:
        assert conn.execute('SELECT title FROM downloads').fetchall() == [('새 제목',)]
    store.remove_from_history('Example', video_id, 'mp4')
    assert store.is_downloaded('Example', video_id, 'webm')
    store.remove_from_history('Example', video_id, 'webm')
    assert not store.is_downloaded('Example', video_id, 'webm')
    assert all(conn.closed for conn in connections)


def test_empty_lookup_does_not_open_connection(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    store = HistoryManager(tmp_path / 'history.db')
    connections.clear()
    assert store.find_downloaded_ids('youtube', ['', None], 'mp4') == set()
    assert not store.is_downloaded('youtube', None, 'mp4')
    assert connections == []


def create_legacy(path):
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('CREATE TABLE downloads (video_id TEXT, format TEXT, title TEXT, uploader TEXT, download_date TEXT)')
        conn.execute('INSERT INTO downloads VALUES (?, ?, ?, ?, ?)', ('id', 'mp4', '기존 제목', '작성자', '2026-10-14'))


def test_legacy_migration_preserves_all_columns_and_closes_connection(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    path = tmp_path / 'history.db'
    create_legacy(path)
    store = HistoryManager(path)
    assert store.is_downloaded('youtube', 'id', 'mp4')
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute('SELECT * FROM downloads').fetchall() == [
            ('youtube', 'id', 'mp4', '기존 제목', '작성자', '2026-10-14')]
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='downloads_old'").fetchall() == []
    assert all(conn.closed for conn in connections)


def test_failed_migration_rolls_back_original_table(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    path = tmp_path / 'history.db'
    create_legacy(path)
    create_table = HistoryManager._create_table
    calls = []

    def fail_after_rename(conn):
        calls.append(conn)
        if len(calls) == 2:
            raise sqlite3.OperationalError('injected disk failure')
        create_table(conn)

    with patch.object(HistoryManager, '_create_table', side_effect=fail_after_rename), patch('data.history_store.log') as log:
        HistoryManager(path)
    log.error.assert_called_once()
    with closing(sqlite3.connect(path)) as conn:
        assert conn.execute('SELECT * FROM downloads').fetchall() == [
            ('id', 'mp4', '기존 제목', '작성자', '2026-10-14')]
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='downloads_old'").fetchall() == []
    assert all(conn.closed for conn in connections)


def test_failed_query_logs_and_never_invents_downloaded_ids(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    store = HistoryManager(tmp_path / 'history.db')
    with closing(sqlite3.connect(store.db_path)) as conn, conn:
        conn.execute('DROP TABLE downloads')
    with patch('data.history_store.log') as log:
        assert store.find_downloaded_ids('youtube', ['x', 'y'], 'mp4') == set()
        assert not store.is_downloaded('youtube', 'x', 'mp4')
    assert log.error.call_count == 2
    assert all(conn.closed for conn in connections)


def test_failed_writes_are_logged_and_connections_closed(tmp_path, tracked_connections):
    connections, _ = tracked_connections
    store = HistoryManager(tmp_path / 'history.db')
    with closing(sqlite3.connect(store.db_path)) as conn, conn:
        conn.execute('DROP TABLE downloads')
    with patch('data.history_store.log') as log:
        store.add_to_history('youtube', 'x', {})
        store.remove_from_history('youtube', 'x')
    assert log.error.call_count == 2
    assert all(conn.closed for conn in connections)
