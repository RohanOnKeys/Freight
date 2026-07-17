"""add pipeline source

Revision ID: df7e1770d883
Revises: 63cb96055e46
Create Date: 2026-07-17 22:06:01.898995
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "df7e1770d883"
down_revision: Union[str, Sequence[str], None] = "63cb96055e46"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    # Add source with a temporary default for existing rows.
    op.add_column(
        "pipelines",
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
            server_default="github",
        ),
    )

    # GitHub metadata is optional for local pipelines.
    op.alter_column(
        "pipelines",
        "repo",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )

    op.alter_column(
        "pipelines",
        "commit_sha",
        existing_type=sa.VARCHAR(length=40),
        nullable=True,
    )

    op.alter_column(
        "pipelines",
        "branch",
        existing_type=sa.VARCHAR(length=255),
        nullable=True,
    )

    # Remove the temporary default.
    op.alter_column(
        "pipelines",
        "source",
        server_default=None,
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "pipelines",
        "branch",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )

    op.alter_column(
        "pipelines",
        "commit_sha",
        existing_type=sa.VARCHAR(length=40),
        nullable=False,
    )

    op.alter_column(
        "pipelines",
        "repo",
        existing_type=sa.VARCHAR(length=255),
        nullable=False,
    )

    op.drop_column("pipelines", "source")