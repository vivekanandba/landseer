"""data integrity: uniqueness constraints, FK indexes, document parent NOT NULL

Revision ID: b2f1c0a94d37
Revises: 30ec096021cb
Create Date: 2026-07-20 00:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2f1c0a94d37"
down_revision: Union[str, None] = "30ec096021cb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Composite uniqueness constraints: (constraint_name, table, columns).
_UNIQUE = (
    ("uq_subdivision_property_name", "subdivisions", ["property_id", "name"]),
    ("uq_neighbor_property_survey", "neighbors", ["property_id", "survey_number"]),
    ("uq_broker_property", "broker_properties", ["broker_id", "property_id"]),
    ("uq_comparison_property", "comparison_items", ["comparison_id", "property_id"]),
)

# Indexes on foreign-key columns used for joins/filtering: (table, column).
_FK_INDEXES = (
    ("subdivisions", "property_id"),
    ("neighbors", "property_id"),
    ("activity_logs", "property_id"),
    ("broker_properties", "property_id"),
    ("comparison_items", "property_id"),
    ("price_history", "property_id"),
    ("survey_boundaries", "property_id"),
    ("survey_boundaries", "neighbor_id"),
)


def upgrade() -> None:
    # A document is always attached to a parent property (the service sets
    # property_id on every create), so no backfill is needed. This assumes no
    # existing row has a NULL property_id; if one did, SET NOT NULL would abort
    # and the offending rows would need a parent assigned first.
    op.alter_column("documents", "property_id", existing_type=sa.Integer(), nullable=False)

    for name, table, columns in _UNIQUE:
        op.create_unique_constraint(name, table, columns)

    for table, column in _FK_INDEXES:
        op.create_index(op.f(f"ix_{table}_{column}"), table, [column], unique=False)


def downgrade() -> None:
    for table, column in _FK_INDEXES:
        op.drop_index(op.f(f"ix_{table}_{column}"), table_name=table)

    for name, table, _columns in _UNIQUE:
        op.drop_constraint(name, table, type_="unique")

    op.alter_column("documents", "property_id", existing_type=sa.Integer(), nullable=True)
