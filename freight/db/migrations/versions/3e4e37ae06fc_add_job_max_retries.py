"""add job max_retries column

Revision ID: 3e4e37ae06fc
Revises: 80da44aee5a4
Create Date: 2026-07-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3e4e37ae06fc"

# Current head
down_revision: Union[str, Sequence[str], None] = "80da44aee5a4"

branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add the max_retries column to jobs.

    Records the retry budget parsed from a pipeline's `retries:` field.
    Existing jobs default to 0 (no retries), matching prior behavior
    where a failed job was always terminal.
    """

    op.add_column(
        "jobs",
        sa.Column(
            "max_retries",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    op.alter_column(
        "jobs",
        "max_retries",
        server_default=None,
    )


def downgrade() -> None:
    """
    Remove the max_retries column.
    """

    op.drop_column(
        "jobs",
        "max_retries",
    )