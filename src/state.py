import sqlite3
import os
from contextlib import contextmanager


class StateDB:
    def __init__(self, data_dir: str):
        self.db_path = os.path.join(data_dir, 'state.db')
        self._init()

    def _init(self):
        with self._conn() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processed_polls (
                    message_id  INTEGER PRIMARY KEY,
                    channel     TEXT    NOT NULL,
                    calendar_id TEXT,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def is_processed(self, message_id: int) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                'SELECT 1 FROM processed_polls WHERE message_id = ?',
                (message_id,)
            ).fetchone()
            return row is not None

    def mark_processed(self, message_id: int, channel: str, calendar_id: str | None = None):
        with self._conn() as conn:
            conn.execute(
                'INSERT OR REPLACE INTO processed_polls (message_id, channel, calendar_id) VALUES (?, ?, ?)',
                (message_id, channel, calendar_id)
            )
