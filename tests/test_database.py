import pytest
from sqlalchemy import text

from recommendation_engine.database import get_engine


def test_get_engine_uses_database_url_env_var(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://rec_engine:rec_engine_dev_pw@localhost:5432/rec_engine_test",
    )
    engine = get_engine()
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).fetchone()[0] == 1


def test_get_engine_explicit_url_overrides_env(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://bogus:bogus@localhost:5432/nonexistent",
    )
    engine = get_engine(
        "postgresql+psycopg://rec_engine:rec_engine_dev_pw@localhost:5432/rec_engine_test"
    )
    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).fetchone()[0] == 1


def test_get_engine_raises_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(KeyError):
        get_engine()
