from sqlalchemy import text

from recommendation_engine.seed import seed


def test_seed_is_idempotent(_migrated_engine):
    with _migrated_engine.connect() as conn:
        before = conn.execute(text("SELECT COUNT(*) FROM properties")).fetchone()[0]
        seed(conn)  # session fixture already seeded once; seed again
        conn.commit()
        after = conn.execute(text("SELECT COUNT(*) FROM properties")).fetchone()[0]
    assert before == after == 6


def test_seed_creates_expected_neighborhoods(temp_conn):
    names = {
        row[0]
        for row in temp_conn.execute(text("SELECT name FROM neighborhoods")).fetchall()
    }
    assert names == {"Chiado", "Alfama", "Príncipe Real", "Parque das Nações", "Cascais Centro", "Almada"}
