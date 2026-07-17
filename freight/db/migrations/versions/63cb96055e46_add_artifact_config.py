"""
Add artifact configuration to jobs.

Revision ID: 63cb96055e46
Revises: 31ffc3d5a55d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "63cb96055e46"
down_revision: Union[str, Sequence[str], None] = "31ffc3d5a55d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add the artifact configuration column to jobs.
    Existing jobs receive an empty JSON object.
    """

    op.add_column(
        "jobs",
        sa.Column(
            "artifacts_config",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
    )

    op.alter_column(
        "jobs",
        "artifacts_config",
        server_default=None,
    )


def downgrade() -> None:
    """
    Remove the artifact configuration column.
    """

    op.drop_column(
        "jobs",
        "artifacts_config",
    )