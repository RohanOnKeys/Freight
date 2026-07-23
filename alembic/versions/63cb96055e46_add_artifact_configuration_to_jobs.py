"""Initial Freight schema.

This was the only migration file in the project and was previously
empty (0 bytes), with no `alembic.ini` or `alembic/env.py` present
either, so `alembic upgrade head` could not do anything. Since this is
also the only revision, it now serves as the full baseline schema,
creating every table Freight's ORM models define: pipelines, runners,
secrets, jobs, and artifacts. It reflects exactly what
`Base.metadata.create_all()` produces from the current models in
`freight/models/`.

Revision ID: 63cb96055e46
Revises:
Create Date: 2026-07-23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "63cb96055e46"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pipelines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("repo", sa.String(length=255), nullable=True),
        sa.Column("commit_sha", sa.String(length=40), nullable=True),
        sa.Column("branch", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_pipelines_id", "pipelines", ["id"],
    )

    op.create_table(
        "runners",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_heartbeat", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("hostname"),
    )
    op.create_index(
        "ix_runners_id", "runners", ["id"],
    )

    op.create_table(
        "secrets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("encrypted_value", sa.String(), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=False),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "ix_secrets_id", "secrets", ["id"],
    )

    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("pipeline_id", sa.Integer(), nullable=False),
        sa.Column("runner_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("stage", sa.String(length=100), nullable=False),
        sa.Column("needs", sa.JSON(), nullable=False),
        sa.Column("image", sa.String(length=255), nullable=False),
        sa.Column("script", sa.JSON(), nullable=False),
        sa.Column("artifacts_config", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retries", sa.Integer(), nullable=False),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["pipeline_id"], ["pipelines.id"]),
        sa.ForeignKeyConstraint(["runner_id"], ["runners.id"]),
    )
    op.create_index(
        "ix_jobs_id", "jobs", ["id"],
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=500), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
    )
    op.create_index(
        "ix_artifacts_id", "artifacts", ["id"],
    )


def downgrade() -> None:
    op.drop_index("ix_artifacts_id", table_name="artifacts")
    op.drop_table("artifacts")

    op.drop_index("ix_jobs_id", table_name="jobs")
    op.drop_table("jobs")

    op.drop_index("ix_secrets_id", table_name="secrets")
    op.drop_table("secrets")

    op.drop_index("ix_runners_id", table_name="runners")
    op.drop_table("runners")

    op.drop_index("ix_pipelines_id", table_name="pipelines")
    op.drop_table("pipelines")