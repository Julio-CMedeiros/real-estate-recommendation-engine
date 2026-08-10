"""API key generation, hashing, and verification for service-to-service auth."""

import hashlib
import secrets

from sqlalchemy import text
from sqlalchemy.engine import Connection


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def create_api_key(conn: Connection, consumer_name: str) -> str:
    raw_key = generate_api_key()
    conn.execute(
        text(
            "INSERT INTO api_keys (consumer_name, hashed_key) "
            "VALUES (:consumer_name, :hashed_key)"
        ),
        {"consumer_name": consumer_name, "hashed_key": hash_key(raw_key)},
    )
    conn.commit()
    return raw_key


def verify_api_key(conn: Connection, raw_key: str) -> str | None:
    row = conn.execute(
        text(
            "SELECT consumer_name FROM api_keys "
            "WHERE hashed_key = :hashed_key AND revoked_at IS NULL"
        ),
        {"hashed_key": hash_key(raw_key)},
    ).mappings().fetchone()
    return row["consumer_name"] if row else None


def revoke_api_key(conn: Connection, consumer_name: str) -> None:
    conn.execute(
        text(
            "UPDATE api_keys SET revoked_at = now() "
            "WHERE consumer_name = :consumer_name AND revoked_at IS NULL"
        ),
        {"consumer_name": consumer_name},
    )
    conn.commit()
