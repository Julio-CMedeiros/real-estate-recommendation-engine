from recommendation_engine.database import get_connection


def test_get_connection_with_explicit_path_seeds_properties(tmp_path):
    conn = get_connection(tmp_path / "explicit.db")
    count = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
    assert count == 6
    conn.close()


def test_get_connection_creates_api_keys_table(temp_conn):
    row = temp_conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"
    ).fetchone()
    assert row is not None


def test_api_keys_table_has_expected_columns(temp_conn):
    cols = {row["name"] for row in temp_conn.execute("PRAGMA table_info(api_keys)")}
    assert cols == {"id", "consumer_name", "hashed_key", "created_at", "revoked_at"}


def test_get_connection_respects_env_override(monkeypatch, tmp_path):
    override_path = tmp_path / "env_override.db"
    monkeypatch.setenv("REC_ENGINE_DB_PATH", str(override_path))
    conn = get_connection()
    assert override_path.exists()
    conn.close()
