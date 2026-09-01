"""Append-only local audit events for visible Jinwoo decisions.

Audit records intentionally contain routing and approval metadata, not raw user
prompts or provider secrets. The user's workspace and model data stay outside
the audit trail unless a future, explicitly approved feature adds a redacted
reference.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .schemas import AuditEvent


class AuditStore:
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
                """CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    mission_id TEXT,
                    actor TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )"""
            )

    def record(self, event_type: str, detail: str, *, mission_id: str | None = None, actor: str = "jinwoo") -> AuditEvent:
        created_at = datetime.now(timezone.utc)
        with self._connect() as connection:
            cursor = connection.execute(
                """INSERT INTO audit_events (event_type, mission_id, actor, detail, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (event_type, mission_id, actor, detail, created_at.isoformat()),
            )
        return AuditEvent(
            id=int(cursor.lastrowid),
            event_type=event_type,
            mission_id=mission_id,
            actor=actor,
            detail=detail,
            created_at=created_at,
        )

    def list(self, limit: int = 100) -> list[AuditEvent]:
        with self._connect() as connection:
            rows = connection.execute(
                """SELECT id, event_type, mission_id, actor, detail, created_at
                   FROM audit_events ORDER BY id DESC LIMIT ?""",
                (limit,),
            ).fetchall()
        return [
            AuditEvent(
                id=row["id"],
                event_type=row["event_type"],
                mission_id=row["mission_id"],
                actor=row["actor"],
                detail=row["detail"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]
