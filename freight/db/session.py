"""
Database engine and session management.

This module initializes the global SQLAlchemy engine, configures the
application session factory, and provides the reusable FastAPI database
dependency used throughout Freight.

The engine maintains the connection pool to the PostgreSQL database,
while ``SessionLocal`` produces short-lived ORM sessions. Each incoming
request receives its own session through ``get_db()``, ensuring proper
transaction isolation and deterministic cleanup.

SQL statement echoing is intentionally disabled. Freight relies on its
own structured application logging rather than emitting every SQL query
to the console.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from freight.core import settings


engine = create_engine(
    settings.POSTGRES_URL,
    echo=False,
)
"""
Global SQLAlchemy engine.

Responsible for creating and managing the application's connection pool
to the PostgreSQL database.
"""


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
"""
Factory for creating SQLAlchemy ORM sessions.

Each invocation returns a new session bound to the global database
engine. Sessions created by this factory are intended to be short-lived
and scoped to a single request or unit of work.
"""


def get_db():
    """
    Provide a database session for the lifetime of a request.

    Intended for use as a FastAPI dependency. A fresh SQLAlchemy session
    is created before the request begins and is guaranteed to be closed
    after the request completes, regardless of whether an exception
    occurs.

    Yields:
        Session:
            An active SQLAlchemy ORM session connected to the Freight
            database.
    """

    db: Session = SessionLocal()

    try:
        yield db

    finally:
        db.close()