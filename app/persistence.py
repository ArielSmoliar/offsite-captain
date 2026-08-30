"""Durable workflow snapshot repositories for the product boundary."""

import json
import sqlite3
from pathlib import Path
from typing import Any, Protocol


class WorkflowRepository(Protocol):
    def load(self, session_hash: str) -> dict[str, Any] | None: ...

    def save(self, session_hash: str, snapshot: dict[str, Any]) -> None: ...


class MemoryWorkflowRepository:
    def __init__(self) -> None:
        self._snapshots: dict[str, dict[str, Any]] = {}

    def load(self, session_hash: str) -> dict[str, Any] | None:
        snapshot = self._snapshots.get(session_hash)
        return json.loads(json.dumps(snapshot)) if snapshot else None

    def save(self, session_hash: str, snapshot: dict[str, Any]) -> None:
        self._snapshots[session_hash] = json.loads(json.dumps(snapshot))


class SqliteWorkflowRepository:
    """Restart-safe local repository; production can implement the same protocol."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS workflow_snapshots (
                session_hash TEXT PRIMARY KEY,
                snapshot_json TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=5)

    def load(self, session_hash: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT snapshot_json FROM workflow_snapshots WHERE session_hash = ?",
                (session_hash,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, session_hash: str, snapshot: dict[str, Any]) -> None:
        payload = json.dumps(snapshot, separators=(",", ":"), sort_keys=True)
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """INSERT INTO workflow_snapshots(session_hash, snapshot_json)
                VALUES (?, ?)
                ON CONFLICT(session_hash) DO UPDATE SET
                    snapshot_json = excluded.snapshot_json,
                    updated_at = CURRENT_TIMESTAMP""",
                (session_hash, payload),
            )
