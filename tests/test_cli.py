import sys

from recommendation_engine.__main__ import main
from recommendation_engine.database import get_connection
from api.auth import verify_api_key


def test_create_key_command_prints_key_and_stores_hash(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "cli_test.db"
    monkeypatch.setattr(
        sys, "argv", ["rec-engine", "create-key", "acme-service", "--db-path", str(db_path)]
    )
    main()
    output = capsys.readouterr().out
    assert "acme-service" in output

    lines = [line for line in output.splitlines() if line.strip()]
    raw_key = lines[-1].split()[-1]
    conn = get_connection(db_path)
    assert verify_api_key(conn, raw_key) == "acme-service"
    conn.close()


def test_run_command_still_works_without_subcommand(monkeypatch, capsys, tmp_path):
    db_path = tmp_path / "run_test.db"
    monkeypatch.setattr(
        sys, "argv", ["rec-engine", "--dry-run", "--json", "--db-path", str(db_path)]
    )
    main()
    output = capsys.readouterr().out
    assert output.strip().startswith("[")
