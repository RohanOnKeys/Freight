"""drop obsolete jobs artifacts column

Revision ID: 80da44aee5a4
Revises: df7e1770d883
Create Date: 2026-07-20 15:19:23.180252

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "80da44aee5a4"

# Current head
down_revision: Union[str, Sequence[str], None] = "df7e1770d883"

branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove the obsolete jobs.artifacts column.

    Artifact configuration is now stored in jobs.artifacts_config.
    Uploaded artifacts are stored in the artifacts table.
    """

    op.drop_column(
        "jobs",
        "artifacts",
    )


def downgrade() -> None:
    """
    Restore the old jobs.artifacts column.
    """

    op.add_column(
        "jobs",
        sa.Column(
            "artifacts",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
    )

    op.alter_column(
        "jobs",
        "artifacts",
        server_default=None,
    )