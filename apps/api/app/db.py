from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, Session, create_engine

from .config import settings
from .models.ingestion import MediaAnalysisEvent


@lru_cache
def get_engine(url: str | None = None):
    engine_url = url or settings.database_url
    connect_args = {"check_same_thread": False} if engine_url.startswith("sqlite") else {}
    return create_engine(engine_url, future=True, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def _ensure_media_analysis_event_context_column(engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    table_name = MediaAnalysisEvent.__tablename__

    with engine.begin() as connection:
        inspector = inspect(connection)
        if table_name not in inspector.get_table_names():
            return

        column_names = {column["name"] for column in inspector.get_columns(table_name)}
        if "context" in column_names:
            return

        # Backfill additive JSON context for older SQLite databases.
        connection.execute(
            text(f"ALTER TABLE {table_name} ADD COLUMN context JSON NOT NULL DEFAULT '{{}}'")
        )


def create_all_models(engine=None) -> None:
    resolved_engine = engine or get_engine()
    SQLModel.metadata.create_all(resolved_engine)
    _ensure_media_analysis_event_context_column(resolved_engine)
