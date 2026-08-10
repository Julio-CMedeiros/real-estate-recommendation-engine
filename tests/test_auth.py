from sqlalchemy import text

from api.auth import create_api_key, revoke_api_key, verify_api_key


def test_create_and_verify_api_key(temp_conn):
    raw_key = create_api_key(temp_conn, "acme-service")
    assert verify_api_key(temp_conn, raw_key) == "acme-service"


def test_verify_rejects_unknown_key(temp_conn):
    assert verify_api_key(temp_conn, "not-a-real-key") is None


def test_verify_rejects_revoked_key(temp_conn):
    raw_key = create_api_key(temp_conn, "acme-service")
    revoke_api_key(temp_conn, "acme-service")
    assert verify_api_key(temp_conn, raw_key) is None


def test_created_keys_are_stored_hashed_not_plaintext(temp_conn):
    raw_key = create_api_key(temp_conn, "acme-service")
    row = temp_conn.execute(
        text("SELECT hashed_key FROM api_keys WHERE consumer_name = :name"),
        {"name": "acme-service"},
    ).mappings().fetchone()
    assert row["hashed_key"] != raw_key
