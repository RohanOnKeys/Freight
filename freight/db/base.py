"""
SQLAlchemy declarative base.

Every ORM model inherits from `Base`, allowing SQLAlchemy to register table
metadata in a single location.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Root declarative class for all database models.
    """

    pass