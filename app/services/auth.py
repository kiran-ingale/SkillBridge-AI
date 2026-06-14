from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

DB_PATH = Path("data/skillbridge.db")


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            token TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()
    return connection


def create_user(email: str, password: str) -> dict[str, str]:
    normalized_email = email.strip().lower()
    if not normalized_email:
        raise ValueError("Email is required.")

    salt = secrets.token_hex(16)
    token = secrets.token_urlsafe(32)
    password_hash = _hash_password(password, salt)
    now = datetime.now(UTC).isoformat()

    try:
        with _connect() as connection:
            connection.execute(
                """
                INSERT INTO users (id, email, password_hash, salt, token, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (secrets.token_urlsafe(16), normalized_email, password_hash, salt, token, now),
            )
            connection.commit()
    except sqlite3.IntegrityError as exc:
        raise ValueError("An account with this email already exists.") from exc

    return {"token": token, "email": normalized_email}


def authenticate_user(email: str, password: str) -> dict[str, str] | None:
    normalized_email = email.strip().lower()
    with _connect() as connection:
        row = connection.execute(
            "SELECT email, password_hash, salt, token FROM users WHERE email = ?",
            (normalized_email,),
        ).fetchone()

    if not row:
        return None

    candidate = _hash_password(password, row["salt"])
    if not hmac.compare_digest(candidate, row["password_hash"]):
        return None

    return {"token": row["token"], "email": row["email"]}


def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return digest.hex()
