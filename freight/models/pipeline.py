"""
Pipeline database model.

Represents a single CI/CD pipeline triggered by a GitHub event.
A pipeline owns one or more jobs that together define the workflow.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from freight.db import Base


class Pipeline(Base):
    """
    ORM model representing a pipeline execution.

    Each GitHub push creates one pipeline. A pipeline contains one or
    more jobs that are executed according to their dependency graph.
    """

    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    repo: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    commit_sha: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    branch: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
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