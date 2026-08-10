"""Shared pytest fixtures: a migrated, seeded Postgres test database.

Base reference data (neighborhoods/properties/price_history/market_snapshots) is
seeded once per test session and treated as read-only by every test. Only
api_keys and recommendations are ever written during a test, so per-test
cleanup only needs to clear those two tables.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine

TEST_DATABASE_URL = "postgresql+psycopg://rec_engine:rec_engine_dev_pw@localhost:5432/rec_engine_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from recommendation_engine.database import get_engine  # noqa: E402 - must follow env var setup
from recommendation_engine.seed import seed  # noqa: E402


@pytest.fixture(scope="session")
def _migrated_engine() -> Engine:
    repo_root = Path(__file__).parent.parent
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=repo_root,
        env={**os.environ, "DATABASE_URL": TEST_DATABASE_URL},
        check=True,
    )
    engine = get_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        seed(conn)
        conn.commit()
    return engine


@pytest.fixture
def temp_conn(_migrated_engine: Engine) -> Connection:
    conn = _migrated_engine.connect()
    yield conn
    try:
        # If a test left this connection in Postgres' aborted-transaction
        # state (e.g. after an IntegrityError), every statement below would
        # otherwise fail with InFailedSqlTransaction. rollback() clears that
        # state; it's a no-op on an already-healthy connection.
        conn.rollback()
        conn.execute(text("DELETE FROM recommendations"))
        conn.execute(text("DELETE FROM api_keys"))
        conn.commit()
    finally:
        conn.close()
