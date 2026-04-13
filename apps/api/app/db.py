from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    """Base class for ORM models."""


def get_engine(url: str, **kwargs: Any):
    """Create an engine for the given URL with future-ready defaults."""

    return create_engine(url, future=True, **kwargs)


def get_session_factory(engine):
    """Create a configurable session factory tied to the provided engine."""

    return sessionmaker(bind=engine, future=True)
