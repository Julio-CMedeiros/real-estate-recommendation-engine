"""Database engine factory."""

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


def get_engine(database_url: str | None = None) -> Engine:
    url = database_url or os.environ["DATABASE_URL"]
    return create_engine(url, pool_size=5, max_overflow=10)
