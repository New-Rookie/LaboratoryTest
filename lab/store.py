"""Evidence store implementation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from lab.models import ExperimentRun


class SQLiteEvidenceStore:
    def __init__(self, db_path: str | Path = "data/experiments.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiment_runs (
                    run_id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    verdict_status TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save_run(self, run: ExperimentRun) -> None:
        payload = run.to_dict()
        verdict_status = run.verdict.status if run.verdict else None
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO experiment_runs
                (run_id, kind, name, status, verdict_status, started_at, ended_at, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run.run_id,
                    run.spec.kind,
                    run.spec.name,
                    run.status,
                    verdict_status,
                    run.started_at,
                    run.ended_at,
                    json.dumps(payload, ensure_ascii=False, indent=2),
                ),
            )
            conn.commit()

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, kind, name, status, verdict_status, started_at, ended_at
                FROM experiment_runs
                ORDER BY started_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "run_id": row[0],
                "kind": row[1],
                "name": row[2],
                "status": row[3],
                "verdict_status": row[4],
                "started_at": row[5],
                "ended_at": row[6],
            }
            for row in rows
        ]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM experiment_runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row[0])
