"""create tariffs and payments

Revision ID: 1792142851
Revises:
Create Date: 2026-10-16 09:20:00
"""

import sqlalchemy as sa
from alembic import op

revision = "1792142851"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tariffs",
        sa.Column("id", sa.String(length=32), primary_key=True),
        sa.Column("title", sa.String(length=64), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
    )
    op.create_table(
        "payments",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("tariff_id", sa.String(length=32), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("discount", sa.BigInteger(), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("installment_months", sa.Integer(), nullable=True),
        sa.Column("schedule", sa.JSON(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["tariff_id"], ["tariffs.id"]),
        sa.UniqueConstraint("idempotency_key"),
    )


def downgrade() -> None:
    op.drop_table("payments")
    op.drop_table("tariffs")
