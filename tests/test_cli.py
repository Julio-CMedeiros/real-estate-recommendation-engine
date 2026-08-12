import sys

from sqlalchemy import text

from recommendation_engine.__main__ import main
from recommendation_engine.database import get_engine
from api.auth import verify_api_key

TEST_DATABASE_URL = "postgresql+psycopg://rec_engine:rec_engine_dev_pw@localhost:5432/rec_engine_test"


def test_create_key_command_prints_key_and_stores_hash(_migrated_engine, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["rec-engine", "create-key", "acme-service", "--database-url", TEST_DATABASE_URL]
    )
    main()
    output = capsys.readouterr().out
    assert "acme-service" in output

    lines = [line for line in output.splitlines() if line.strip()]
    raw_key = lines[-1].split()[-1]
    engine = get_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        assert verify_api_key(conn, raw_key) == "acme-service"
        conn.execute(text("DELETE FROM api_keys WHERE consumer_name = 'acme-service'"))
        conn.commit()


def test_run_command_still_works_without_subcommand(_migrated_engine, monkeypatch, capsys):
    monkeypatch.setattr(
        sys, "argv", ["rec-engine", "--dry-run", "--json", "--database-url", TEST_DATABASE_URL]
    )
    main()
    output = capsys.readouterr().out
    assert output.strip().startswith("[")


def test_seed_db_command_is_idempotent(_migrated_engine, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["rec-engine", "seed-db", "--database-url", TEST_DATABASE_URL])
    main()
    first_output = capsys.readouterr().out
    main()
    second_output = capsys.readouterr().out
    assert "Seed data applied." in first_output
    assert "Seed data applied." in second_output

    engine = get_engine(TEST_DATABASE_URL)
    with engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM properties")).fetchone()[0]
    assert count == 6


def test_backtest_command_prints_report(_migrated_engine, monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["rec-engine", "backtest", "--database-url", TEST_DATABASE_URL])
    main()
    output = capsys.readouterr().out
    assert "T01R01" in output
    assert "T01R02" in output
    assert "sample" in output.lower()
