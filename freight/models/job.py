"""
Job database model.

Represents an individual unit of work within a pipeline. Jobs define the
Docker image to execute, the commands to run, their dependencies and
their execution state.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from freight.db import Base


class Job(Base):
    """
    ORM model representing a pipeline job.

    Every job belongs to a single pipeline and may be assigned to a runner
    for execution. Jobs can depend on other jobs through the `needs` field,
    allowing the scheduler to build and execute a directed acyclic graph.
    """

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    pipeline_id: Mapped[int] = mapped_column(
        ForeignKey("pipelines.id"),
        nullable=False,
    )

    runner_id: Mapped[int | None] = mapped_column(
        ForeignKey("runners.id"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    stage: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    needs: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    image: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    script: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
    )

    artifacts_config: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
    )

    retries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    exit_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    pipeline = relationship(
        "Pipeline",
        back_populates="jobs",
    )

    runner = relationship(
        "Runner",
        back_populates="jobs",
    )

    artifacts = relationship(
        "Artifact",
        back_populates="job",
        cascade="all, delete-orphan",
    )