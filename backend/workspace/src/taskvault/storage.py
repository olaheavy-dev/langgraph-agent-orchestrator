"""SQLite persistence.

One connection, one writer. The concurrency ceiling this implies is deliberate
and documented in adr-001-storage; do not add a connection pool without
revisiting that decision first.
"""

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from taskvault.models import Status, Task

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'open',
    owner_key  TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL
);
"""


class TaskStore:
    def __init__(self, path: Path | str = ':memory:') -> None:
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(SCHEMA)

    def _row_to_task(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row['id'],
            title=row['title'],
            status=Status(row['status']),
            owner_key=row['owner_key'],
            created_at=datetime.fromisoformat(row['created_at']),
        )

    def create(self, title: str, owner_key: str) -> Task:
        cursor = self._connection.execute(
            'INSERT INTO tasks (title, owner_key, created_at) VALUES (?, ?, ?)',
            (title, owner_key, datetime.now(UTC).isoformat()),
        )
        self._connection.commit()
        return self.get(cursor.lastrowid, owner_key)  # type: ignore[arg-type]

    def get(self, task_id: int, owner_key: str) -> Task | None:
        row = self._connection.execute(
            'SELECT * FROM tasks WHERE id = ? AND owner_key = ?', (task_id, owner_key)
        ).fetchone()
        return self._row_to_task(row) if row else None

    def list(self, owner_key: str, status: Status | None = None) -> list[Task]:
        rows = self._connection.execute(
            'SELECT * FROM tasks WHERE owner_key = ? ORDER BY id', (owner_key,)
        ).fetchall()
        return [self._row_to_task(row) for row in rows]

    def complete(self, task_id: int, owner_key: str) -> Task | None:
        self._connection.execute(
            "UPDATE tasks SET status = 'done' WHERE id = ? AND owner_key = ?",
            (task_id, owner_key),
        )
        self._connection.commit()
        return self.get(task_id, owner_key)
