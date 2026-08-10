import threading

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


def test_concurrent_first_access_does_not_raise(tmp_path):
    """Regression test for the cold-start seeding race.

    Multiple threads (as FastAPI's threadpool would spawn) calling
    get_connection() against the same brand-new, nonexistent DB path can
    each observe `needs_seed=True` and each attempt to run `_seed()`,
    which previously crashed with `sqlite3.OperationalError: table
    neighborhoods already exists` for every thread that lost the race.
    """
    path = tmp_path / "concurrent.db"
    errors: list[BaseException] = []
    lock = threading.Lock()

    def worker() -> None:
        try:
            conn = get_connection(path)
            conn.execute("SELECT COUNT(*) FROM properties").fetchone()
            conn.close()
        except BaseException as exc:  # noqa: BLE001 - capture for assertion
            with lock:
                errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"concurrent get_connection() raised: {errors!r}"

    # Seeding must have happened exactly once - no duplicated rows.
    conn = get_connection(path)
    count = conn.execute("SELECT COUNT(*) FROM properties").fetchone()[0]
    conn.close()
    assert count == 6
