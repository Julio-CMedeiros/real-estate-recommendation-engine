"""Shared pytest fixtures: an isolated, per-test SQLite database."""

import sqlite3
from pathlib import Path

import pytest

from recommendation_engine.database import get_connection


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"


@pytest.fixture
def temp_conn(temp_db_path: Path) -> sqlite3.Connection:
    conn = get_connection(temp_db_path)
    yield conn
    conn.close()
