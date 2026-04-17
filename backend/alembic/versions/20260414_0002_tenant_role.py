"""add tenant role

Revision ID: 20260414_0002
Revises: 20260414_0001
Create Date: 2026-04-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "20260414_0002"
down_revision = "20260414_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("role", sa.String(length=32), nullable=True))
    op.execute("UPDATE tenants SET role = 'owner' WHERE role IS NULL")
    op.alter_column("tenants", "role", nullable=False)


def downgrade() -> None:
    op.drop_column("tenants", "role")
