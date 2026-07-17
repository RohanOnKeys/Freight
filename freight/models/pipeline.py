"""
Pipeline database model.

Represents a single CI/CD pipeline execution regardless of how it was
triggered (GitHub webhook, local CLI, API, etc.). A pipeline owns one
or more jobs that together define the workflow.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from freight.db import Base


class Pipeline(Base):
    """
    ORM model representing a pipeline execution.

    A pipeline may originate from multiple ingestion sources such as
    GitHub, a local CLI invocation, or future integrations. Each
    pipeline contains one or more jobs executed according to their
    dependency graph.
    """

    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    repo: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    commit_sha: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    branch: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    jobs = relationship(
        "Job",
        back_populates="pipeline",
        cascade="all, delete-orphan",
    )