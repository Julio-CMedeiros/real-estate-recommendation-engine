"""API key generation, hashing, and verification for service-to-service auth."""

import hashlib
import secrets
import sqlite3


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_api_key(conn: sqlite3.Connection, consumer_name: str) -> str:
    raw_key = generate_api_key()
    conn.execute(
        "INSERT INTO api_keys (consumer_name, hashed_key) VALUES (?, ?)",
        [consumer_name, hash_key(raw_key)],
    )
    conn.commit()
    return raw_key


def verify_api_key(conn: sqlite3.Connection, raw_key: str) -> str | None:
    row = conn.execute(
        "SELECT consumer_name FROM api_keys WHERE hashed_key = ? AND revoked_at IS NULL",
        [hash_key(raw_key)],
    ).fetchone()
    return row["consumer_name"] if row else None


def revoke_api_key(conn: sqlite3.Connection, consumer_name: str) -> None:
    conn.execute(
        "UPDATE api_keys SET revoked_at = datetime('now') "
        "WHERE consumer_name = ? AND revoked_at IS NULL",
        [consumer_name],
    )
    conn.commit()
