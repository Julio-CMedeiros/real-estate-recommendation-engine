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


def test_seed_advances_identity_sequences_for_future_inserts(temp_conn):
    """seed() inserts explicit ids 1-6 into neighborhoods/properties. Without
    re-syncing the backing identity sequences, a later insert that omits an
    id would draw nextval() = 1 and collide with the seeded row 1
    (duplicate key value violates unique constraint).
    """
    seed(temp_conn)

    # No explicit id: must draw a fresh value from the (now-advanced) sequence.
    new_neighborhood_id = temp_conn.execute(
        text("INSERT INTO neighborhoods (name, city) VALUES ('Test Neighborhood', 'Test City') RETURNING id")
    ).scalar_one()
    assert new_neighborhood_id > 6

    new_property_id = temp_conn.execute(
        text(
            "INSERT INTO properties "
            "(neighborhood_id, title, type, price, area_m2, bedrooms, bathrooms, listed_date, status) "
            "VALUES (:neighborhood_id, 'Test Property', 'apartment', 100000, 50, 1, 1, '2026-08-10', 'active') "
            "RETURNING id"
        ),
        {"neighborhood_id": new_neighborhood_id},
    ).scalar_one()
    assert new_property_id > 6
