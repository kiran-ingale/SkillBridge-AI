from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

DB_PATH = Path("data/skillbridge.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS diagnoses (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            profile_json TEXT NOT NULL,
            result_json TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS progress_tasks (
            id TEXT PRIMARY KEY,
            diagnosis_id TEXT NOT NULL,
            created_at TEXT NOT NULL,
            title TEXT NOT NULL,
            status TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (diagnosis_id) REFERENCES diagnoses(id)
        )
        """
    )
    connection.commit()
    return connection


def save_diagnosis(profile: dict[str, Any], result: dict[str, Any]) -> str:
    diagnosis_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    with _connect() as connection:
        connection.execute(
            "INSERT INTO diagnoses (id, created_at, profile_json, result_json) VALUES (?, ?, ?, ?)",
            (diagnosis_id, now, json.dumps(profile), json.dumps(result)),
        )
        connection.commit()
    return diagnosis_id


def list_diagnoses() -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, created_at, profile_json, result_json FROM diagnoses ORDER BY created_at DESC LIMIT 25"
        ).fetchall()
    return [_diagnosis_row_to_dict(row) for row in rows]


def get_diagnosis(diagnosis_id: str) -> dict[str, Any] | None:
    with _connect() as connection:
        row = connection.execute(
            "SELECT id, created_at, profile_json, result_json FROM diagnoses WHERE id = ?",
            (diagnosis_id,),
        ).fetchone()
    return _diagnosis_row_to_dict(row) if row else None


def save_progress_task(diagnosis_id: str, title: str, status: str, notes: str = "") -> dict[str, Any]:
    task_id = str(uuid4())
    now = datetime.now(UTC).isoformat()
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO progress_tasks (id, diagnosis_id, created_at, title, status, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (task_id, diagnosis_id, now, title, status, notes),
        )
        connection.commit()
    return {
        "id": task_id,
        "diagnosis_id": diagnosis_id,
        "created_at": now,
        "title": title,
        "status": status,
        "notes": notes,
    }


def list_progress_tasks(diagnosis_id: str) -> list[dict[str, Any]]:
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, diagnosis_id, created_at, title, status, notes
            FROM progress_tasks
            WHERE diagnosis_id = ?
            ORDER BY created_at DESC
            """,
            (diagnosis_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def _diagnosis_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    profile = json.loads(row["profile_json"])
    result = json.loads(row["result_json"])
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "student_name": profile.get("name"),
        "target_role": profile.get("target_role"),
        "employability_score": result.get("employability_score"),
        "role_readiness_score": result.get("role_readiness_score"),
        "recommended_duration_days": result.get("recommended_duration_days"),
        "profile": profile,
        "result": result,
    }
