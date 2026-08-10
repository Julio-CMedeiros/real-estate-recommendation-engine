"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-10
"""

import sqlalchemy as sa

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "neighborhoods",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("city", sa.Text, nullable=False),
    )

    op.create_table(
        "properties",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("neighborhood_id", sa.Integer, sa.ForeignKey("neighborhoods.id")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("area_m2", sa.Float, nullable=False),
        sa.Column("bedrooms", sa.Integer),
        sa.Column("bathrooms", sa.Integer),
        sa.Column("floor", sa.Integer),
        sa.Column("has_parking", sa.Integer, server_default="0"),
        sa.Column("has_terrace", sa.Integer, server_default="0"),
        sa.Column("energy_rating", sa.Text),
        sa.Column("listed_date", sa.Text, nullable=False),
        sa.Column("status", sa.Text, server_default="active"),
        sa.Column("description", sa.Text),
    )

    op.create_table(
        "price_history",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id")),
        sa.Column("price", sa.Float, nullable=False),
        sa.Column("changed_date", sa.Text, nullable=False),
        sa.Column("event", sa.Text, server_default="price_change"),
        sa.UniqueConstraint(
            "property_id", "changed_date", "event",
            name="uq_price_history_property_date_event",
        ),
    )

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("neighborhood_id", sa.Integer, sa.ForeignKey("neighborhoods.id")),
        sa.Column("month", sa.Text, nullable=False),
        sa.Column("avg_price_m2", sa.Float),
        sa.Column("listings_count", sa.Integer),
        sa.Column("avg_days_on_market", sa.Integer),
        sa.Column("sold_count", sa.Integer),
        sa.UniqueConstraint(
            "neighborhood_id", "month",
            name="uq_market_snapshots_neighborhood_month",
        ),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("consumer_name", sa.Text, nullable=False),
        sa.Column("hashed_key", sa.Text, nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.Text, nullable=False),
        sa.Column("type", sa.Text, nullable=False),
        sa.Column("priority", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("property_id", sa.Integer, sa.ForeignKey("properties.id")),
        sa.Column("version", sa.Text),
        sa.Column("created_at", sa.DateTime, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("api_keys")
    op.drop_table("market_snapshots")
    op.drop_table("price_history")
    op.drop_table("properties")
    op.drop_table("neighborhoods")
