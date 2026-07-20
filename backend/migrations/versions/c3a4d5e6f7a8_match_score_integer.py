"""match_score: Float -> Integer

Revision ID: c3a4d5e6f7a8
Revises: b2f1c0a94d37
Create Date: 2026-07-20 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a4d5e6f7a8"
down_revision: Union[str, None] = "b2f1c0a94d37"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # match_score always holds a rounded 0–100 int; store it as INTEGER.
    # postgresql_using casts existing float values (double precision -> integer
    # is not an implicit cast, so it must be spelled out).
    op.alter_column(
        "properties",
        "match_score",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="match_score::integer",
    )


def downgrade() -> None:
    op.alter_column(
        "properties",
        "match_score",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="match_score::double precision",
    )
