from sqlalchemy import text

from recommendation_engine.engine.runner import run_engine


def test_run_engine_dry_run_does_not_persist(temp_conn):
    run_engine(temp_conn, dry_run=True)
    count = temp_conn.execute(text("SELECT COUNT(*) FROM recommendations")).fetchone()[0]
    assert count == 0


def test_run_engine_persists_when_not_dry_run(temp_conn):
    recs = run_engine(temp_conn, dry_run=False)
    count = temp_conn.execute(text("SELECT COUNT(*) FROM recommendations")).fetchone()[0]
    assert count == len(recs)
    assert count > 0


def test_run_engine_filters_by_property_id(temp_conn):
    recs = run_engine(temp_conn, property_id=1, dry_run=True)
    assert all(r.property_id == 1 for r in recs)
