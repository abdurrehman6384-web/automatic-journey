"""Local, consent-based SQLite memory. Cloud memory is optional, never required."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .schemas import MemoryItem


class LocalMemoryStore:
    def __init__(self, data_dir: Path) -> None:
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "jinwoo.db"
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def add(self, content: str, kind: str) -> MemoryItem:
        created_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO memories (content, kind, created_at) VALUES (?, ?, ?)",
                (content, kind, created_at.isoformat()),
            )
        return MemoryItem(id=int(cursor.lastrowid), content=content, kind=kind, created_at=created_at)

    def list(self, limit: int = 100) -> list[MemoryItem]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT id, content, kind, created_at FROM memories ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            MemoryItem(id=row["id"], content=row["content"], kind=row["kind"], created_at=datetime.fromisoformat(row["created_at"]))
            for row in rows
        ]

    def update(self, memory_id: int, content: str, kind: str) -> MemoryItem | None:
        with self._connect() as connection:
            cursor = connection.execute(
                "UPDATE memories SET content = ?, kind = ? WHERE id = ?",
                (content, kind, memory_id),
            )
            if cursor.rowcount == 0:
                return None
            row = connection.execute(
                "SELECT id, content, kind, created_at FROM memories WHERE id = ?", (memory_id,)
            ).fetchone()
        if row is None:  # defensive: the successful UPDATE must have a row
            return None
        return MemoryItem(
            id=row["id"],
            content=row["content"],
            kind=row["kind"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def delete(self, memory_id: int) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        return cursor.rowcount > 0
