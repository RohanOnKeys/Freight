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
    """
    Number of retry attempts already made after an initial failure.
    Incremented by `freight.core.retry.handle_job_failure` each time a
    failed job is transparently requeued. Compared against
    `max_retries` to decide whether another attempt is allowed.
    """

    max_retries: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    """
    Maximum number of retry attempts allowed for this job, parsed from
    the pipeline's `retries:` field (0 if the field is omitted, meaning
    a failed execution is always terminal).
    """

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

    @property
    def repo(self) -> str | None:
        """
        Repository this job's source belongs to, if any.

        Proxies to the parent pipeline, since GitHub source metadata is
        recorded once per pipeline rather than duplicated per job. Read
        by the runner (via the `/jobs/{id}` API response) to know what
        to `git fetch` before executing the job's script. `None` for
        pipelines not triggered by a GitHub push (for example, local
        CLI runs).
        """
        return self.pipeline.repo if self.pipeline else None

    @property
    def branch(self) -> str | None:
        """
        Branch this job's source was pushed on, if any.

        Proxies to the parent pipeline. `None` for pipelines not
        triggered by a GitHub push.
        """
        return self.pipeline.branch if self.pipeline else None

    @property
    def commit_sha(self) -> str | None:
        """
        Exact commit this job's source should be checked out at, if any.

        Proxies to the parent pipeline. The runner fetches and checks
        out exactly this commit before executing the job's script.
        `None` for pipelines not triggered by a GitHub push.
        """
        return self.pipeline.commit_sha if self.pipeline else None