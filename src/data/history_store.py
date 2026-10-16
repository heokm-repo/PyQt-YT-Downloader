"""SQLite history, with bounded batch queries and explicit connection lifetimes."""
from contextlib import closing
import datetime
import os
import sqlite3

from constants import DEFAULT_FORMAT, HISTORY_DB_FILENAME, HISTORY_TABLE_NAME, DATE_FORMAT
from utils.app_paths import get_user_data_path
from utils.logger import log


# Leave room for extractor/format even on SQLite builds with a 999-variable limit.
HISTORY_QUERY_BATCH_SIZE = 900


class HistoryManager:
    def __init__(self, db_path=None):
        self.db_path = str(db_path) if db_path is not None else os.path.join(get_user_data_path(), HISTORY_DB_FILENAME)
        self._init_db()

    @staticmethod
    def _create_table(conn):
        conn.execute(f'''CREATE TABLE IF NOT EXISTS {HISTORY_TABLE_NAME} (
            extractor TEXT, video_id TEXT, format TEXT, title TEXT,
            uploader TEXT, download_date TEXT,
            PRIMARY KEY (extractor, video_id, format))''')

    def _init_db(self):
        try:
            with closing(sqlite3.connect(self.db_path)) as conn, conn:
                # Include DDL in the transaction so a failed migration rolls back.
                conn.execute('BEGIN')
                self._create_table(conn)
                self._migrate_db(conn)
        except Exception as exc:
            log.error(f"DB 초기화 오류: {exc}", exc_info=True)

    def _migrate_db(self, conn):
        columns = [row[1] for row in conn.execute(f'PRAGMA table_info({HISTORY_TABLE_NAME})')]
        if 'extractor' in columns:
            return
        log.info('DB 마이그레이션: extractor 컬럼 추가 중...')
        conn.execute(f'ALTER TABLE {HISTORY_TABLE_NAME} RENAME TO {HISTORY_TABLE_NAME}_old')
        self._create_table(conn)
        conn.execute(f'''INSERT INTO {HISTORY_TABLE_NAME}
            (extractor, video_id, format, title, uploader, download_date)
            SELECT 'youtube', video_id, format, title, uploader, download_date
            FROM {HISTORY_TABLE_NAME}_old''')
        conn.execute(f'DROP TABLE {HISTORY_TABLE_NAME}_old')
        log.info('DB 마이그레이션 완료')

    def find_downloaded_ids(self, extractor, video_ids, fmt):
        """Return matching IDs for one extractor/format using one connection.

        Repeated input IDs share a lookup. Errors are logged and do not invent
        matches, preserving the single-query false-on-error policy.
        """
        ids = list(dict.fromkeys(video_id for video_id in video_ids if video_id))
        found = set()
        if not ids:
            return found
        try:
            with closing(sqlite3.connect(self.db_path)) as conn:
                variable_limit = (conn.getlimit(sqlite3.SQLITE_LIMIT_VARIABLE_NUMBER)
                                  if hasattr(conn, 'getlimit') else 999)
                batch_size = min(HISTORY_QUERY_BATCH_SIZE, variable_limit - 2)
                if batch_size < 1:
                    raise sqlite3.OperationalError('SQLite variable limit is too small for history lookup')
                for start in range(0, len(ids), batch_size):
                    batch = ids[start:start + batch_size]
                    placeholders = ','.join('?' for _ in batch)
                    rows = conn.execute(
                        f'SELECT video_id FROM {HISTORY_TABLE_NAME} '
                        f'WHERE extractor = ? AND format = ? AND video_id IN ({placeholders})',
                        (extractor, fmt, *batch),
                    )
                    found.update(row[0] for row in rows)
        except Exception as exc:
            log.error(f'DB 검색 오류 (extractor={extractor}, fmt={fmt}): {exc}', exc_info=True)
        return found

    def is_downloaded(self, extractor, video_id, fmt):
        return bool(video_id) and video_id in self.find_downloaded_ids(extractor, [video_id], fmt)

    def add_to_history(self, extractor, video_id, meta, fmt=DEFAULT_FORMAT):
        if not video_id:
            return
        try:
            with closing(sqlite3.connect(self.db_path)) as conn, conn:
                conn.execute(
                    f'INSERT OR REPLACE INTO {HISTORY_TABLE_NAME} '
                    '(extractor, video_id, format, title, uploader, download_date) VALUES (?, ?, ?, ?, ?, ?)',
                    (extractor, video_id, fmt, meta.get('title', ''), meta.get('uploader', ''),
                     datetime.datetime.now().strftime(DATE_FORMAT)),
                )
        except Exception as exc:
            log.error(f'DB 저장 오류 (extractor={extractor}, video_id={video_id}, fmt={fmt}): {exc}', exc_info=True)

    def remove_from_history(self, extractor, video_id, fmt=DEFAULT_FORMAT):
        if not video_id:
            return
        try:
            with closing(sqlite3.connect(self.db_path)) as conn, conn:
                conn.execute(
                    f'DELETE FROM {HISTORY_TABLE_NAME} WHERE extractor = ? AND video_id = ? AND format = ?',
                    (extractor, video_id, fmt),
                )
            log.info(f'Removed from history: {extractor}/{video_id} (format={fmt})')
        except Exception as exc:
            log.error(f'DB 삭제 오류 (extractor={extractor}, video_id={video_id}, fmt={fmt}): {exc}', exc_info=True)
