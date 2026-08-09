"""SQLite database with Lisbon metro area seed data."""

import os
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "demo.db"


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    if db_path is not None:
        path = Path(db_path)
    else:
        path = Path(os.environ.get("REC_ENGINE_DB_PATH", str(DB_PATH)))
    needs_seed = not path.exists()
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    if needs_seed:
        _seed(conn)
    _ensure_api_keys_table(conn)
    return conn


def _ensure_api_keys_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY,
            consumer_name TEXT NOT NULL,
            hashed_key TEXT NOT NULL UNIQUE,
            created_at TEXT DEFAULT (datetime('now')),
            revoked_at TEXT
        )
        """
    )
    conn.commit()


def _seed(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE neighborhoods (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            city TEXT NOT NULL
        );

        CREATE TABLE properties (
            id INTEGER PRIMARY KEY,
            neighborhood_id INTEGER REFERENCES neighborhoods(id),
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            price REAL NOT NULL,
            area_m2 REAL NOT NULL,
            bedrooms INTEGER,
            bathrooms INTEGER,
            floor INTEGER,
            has_parking INTEGER DEFAULT 0,
            has_terrace INTEGER DEFAULT 0,
            energy_rating TEXT,
            listed_date TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            description TEXT
        );

        CREATE TABLE price_history (
            id INTEGER PRIMARY KEY,
            property_id INTEGER REFERENCES properties(id),
            price REAL NOT NULL,
            changed_date TEXT NOT NULL,
            event TEXT DEFAULT 'price_change'
        );

        CREATE TABLE market_snapshots (
            id INTEGER PRIMARY KEY,
            neighborhood_id INTEGER REFERENCES neighborhoods(id),
            month TEXT NOT NULL,
            avg_price_m2 REAL,
            listings_count INTEGER,
            avg_days_on_market INTEGER,
            sold_count INTEGER
        );

        INSERT INTO neighborhoods VALUES
            (1, 'Chiado', 'Lisbon'),
            (2, 'Alfama', 'Lisbon'),
            (3, 'Príncipe Real', 'Lisbon'),
            (4, 'Parque das Nações', 'Lisbon'),
            (5, 'Cascais Centro', 'Cascais'),
            (6, 'Almada', 'Almada');

        INSERT INTO properties (id, neighborhood_id, title, type, price, area_m2, bedrooms, bathrooms, floor, has_parking, has_terrace, energy_rating, listed_date, status) VALUES
            (1, 1, 'Renovated Chiado Apartment', 'apartment', 520000, 85, 2, 1, 3, 0, 0, 'B', '2026-02-15', 'active'),
            (2, 1, 'Chiado Penthouse', 'penthouse', 980000, 140, 3, 2, 6, 1, 1, 'A', '2026-01-10', 'active'),
            (3, 2, 'Alfama Traditional Flat', 'apartment', 310000, 65, 1, 1, 2, 0, 0, 'D', '2026-03-01', 'active'),
            (4, 4, 'Expo T3 River View', 'apartment', 450000, 95, 3, 2, 8, 1, 1, 'A', '2026-03-10', 'active'),
            (5, 6, 'Almada T2 with Parking', 'apartment', 185000, 72, 2, 1, 5, 1, 0, 'B', '2026-03-15', 'active'),
            (6, 3, 'Príncipe Real Garden Flat', 'apartment', 680000, 110, 3, 2, 2, 1, 1, 'B', '2025-12-05', 'active');

        INSERT INTO price_history (property_id, price, changed_date, event) VALUES
            (1, 545000, '2026-02-15', 'listed'),
            (1, 520000, '2026-03-20', 'price_change'),
            (2, 980000, '2026-01-10', 'listed'),
            (6, 720000, '2025-12-05', 'listed'),
            (6, 680000, '2026-02-15', 'price_change');

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
            (6, '2026-04', 2240, 122, 62, 41);
        """
    )
    conn.commit()
