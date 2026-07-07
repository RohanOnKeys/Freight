"""
Secret database model.

Stores encrypted secrets used during job execution. Secrets are encrypted
before being written to the database and are only decrypted in memory when
a runner requests them.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from freight.db import Base


class Secret(Base):
    """
    ORM model representing an encrypted secret.

    Secrets are scoped to a repository or project and injected into Docker
    containers as environment variables at runtime.
    """

    __tablename__ = "secrets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    encrypted_value: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    scope: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )