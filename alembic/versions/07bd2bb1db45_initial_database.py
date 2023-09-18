"""Initial Database.

Revision ID: 07bd2bb1db45
Revises:
Create Date: 2023-09-12 16:46:41.878075
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "07bd2bb1db45"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the tests table."""
    op.create_table(
        "tests",
        sa.Column("id", sa.String(), nullable=False, primary_key=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=True, onupdate=sa.func.now()),
        sa.Column("spec", JSONB(), nullable=True),
        sa.Column("report", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Drop the tests table."""
    op.drop_table("tests")
