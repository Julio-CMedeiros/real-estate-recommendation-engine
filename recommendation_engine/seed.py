"""Idempotent seeding of the Lisbon metro area demo dataset.

Does not call conn.commit() - the caller owns the transaction boundary
(contrast create_api_key/_persist, which self-commit after their work).
"""

from sqlalchemy import text
from sqlalchemy.engine import Connection


def seed(conn: Connection) -> None:
    conn.execute(text(
        """
        INSERT INTO neighborhoods (id, name, city) VALUES
            (1, 'Chiado', 'Lisbon'),
            (2, 'Alfama', 'Lisbon'),
            (3, 'Príncipe Real', 'Lisbon'),
            (4, 'Parque das Nações', 'Lisbon'),
            (5, 'Cascais Centro', 'Cascais'),
            (6, 'Almada', 'Almada')
        ON CONFLICT (id) DO NOTHING
        """
    ))

    conn.execute(text(
        """
        INSERT INTO properties (id, neighborhood_id, title, type, price, area_m2, bedrooms, bathrooms, floor, has_parking, has_terrace, energy_rating, listed_date, status) VALUES
            (1, 1, 'Renovated Chiado Apartment', 'apartment', 520000, 85, 2, 1, 3, 0, 0, 'B', '2026-02-15', 'active'),
            (2, 1, 'Chiado Penthouse', 'penthouse', 980000, 140, 3, 2, 6, 1, 1, 'A', '2026-01-10', 'active'),
            (3, 2, 'Alfama Traditional Flat', 'apartment', 310000, 65, 1, 1, 2, 0, 0, 'D', '2026-03-01', 'active'),
            (4, 4, 'Expo T3 River View', 'apartment', 450000, 95, 3, 2, 8, 1, 1, 'A', '2026-03-10', 'active'),
            (5, 6, 'Almada T2 with Parking', 'apartment', 185000, 72, 2, 1, 5, 1, 0, 'B', '2026-03-15', 'active'),
            (6, 3, 'Príncipe Real Garden Flat', 'apartment', 680000, 110, 3, 2, 2, 1, 1, 'B', '2025-12-05', 'active')
        ON CONFLICT (id) DO NOTHING
        """
    ))

    conn.execute(text(
        """
        INSERT INTO price_history (property_id, price, changed_date, event) VALUES
            (1, 545000, '2026-02-15', 'listed'),
            (1, 520000, '2026-03-20', 'price_change'),
            (2, 980000, '2026-01-10', 'listed'),
            (6, 720000, '2025-12-05', 'listed'),
            (6, 680000, '2026-02-15', 'price_change')
        ON CONFLICT (property_id, changed_date, event) DO NOTHING
        """
    ))

    conn.execute(text(
        """
        INSERT INTO market_snapshots (neighborhood_id, month, avg_price_m2, listings_count, avg_days_on_market, sold_count) VALUES
            (1, '2025-11', 5800, 45, 62, 12),
            (1, '2025-12', 5850, 42, 58, 14),
            (1, '2026-01', 5920, 48, 55, 16),
            (1, '2026-02', 6010, 51, 52, 18),
            (1, '2026-03', 6100, 47, 48, 20),
            (1, '2026-04', 6180, 50, 45, 19),
            (4, '2025-11', 4200, 78, 45, 28),
            (4, '2025-12', 4250, 72, 42, 30),
            (4, '2026-01', 4300, 80, 40, 32),
            (4, '2026-02', 4380, 85, 38, 35),
            (4, '2026-03', 4450, 82, 36, 33),
            (4, '2026-04', 4520, 79, 35, 31),
            (6, '2025-11', 2100, 120, 75, 35),
            (6, '2025-12', 2120, 115, 72, 38),
            (6, '2026-01', 2150, 125, 70, 40),
            (6, '2026-02', 2180, 130, 68, 42),
            (6, '2026-03', 2200, 128, 65, 44),
            (6, '2026-04', 2240, 122, 62, 41)
        ON CONFLICT (neighborhood_id, month) DO NOTHING
        """
    ))

    # Explicit-id inserts above do NOT advance the identity sequences backing
    # neighborhoods.id / properties.id (SERIAL columns), so a later insert that
    # omits an id would draw nextval() = 1 and collide with the seeded rows.
    # Re-sync the sequences to the current max id. Idempotent and safe to call
    # every time seed() runs.
    conn.execute(text(
        "SELECT setval(pg_get_serial_sequence('neighborhoods', 'id'), "
        "COALESCE((SELECT MAX(id) FROM neighborhoods), 1))"
    ))
    conn.execute(text(
        "SELECT setval(pg_get_serial_sequence('properties', 'id'), "
        "COALESCE((SELECT MAX(id) FROM properties), 1))"
    ))
