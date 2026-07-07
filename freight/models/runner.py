"""
Runner database model.

Represents a worker node responsible for executing jobs.
Each runner periodically sends heartbeats to indicate that it is alive
and available to receive work.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from freight.db import Base


class Runner(Base):
    """
    ORM model representing a registered runner.

    A runner can execute many jobs throughout its lifetime. The scheduler
    assigns queued jobs to available runners.
    """

    __tablename__ = "runners"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    hostname: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="idle",
    )

    last_heartbeat: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    jobs = relationship(
        "Job",
        back_populates="runner",
    )