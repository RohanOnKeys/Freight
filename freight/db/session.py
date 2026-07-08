"""
Database engine and session management.

This module creates the SQLAlchemy engine, configures the session factory,
and provides a reusable database dependency for FastAPI routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from freight.core import settings
from sqlalchemy.orm import Session


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

engine = create_engine(
    settings.POSTGRES_URL,
    echo=True,
)
"""
Global SQLAlchemy engine.

Responsible for managing connections to the PostgreSQL database.
"""


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
"""
Factory used to create database sessions.
"""


def get_db():
    """
    Creates a database session for the duration of a request.

    Yields:
        Session:
            An active SQLAlchemy session.

    Ensures:
        The session is always closed after use.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()