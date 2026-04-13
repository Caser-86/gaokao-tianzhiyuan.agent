from collections.abc import Generator
from functools import lru_cache

from sqlmodel import SQLModel, Session, create_engine

from .config import settings


@lru_cache
def get_engine(url: str | None = None):
    engine_url = url or settings.database_url
    connect_args = {"check_same_thread": False} if engine_url.startswith("sqlite") else {}
    return create_engine(engine_url, future=True, connect_args=connect_args)


def get_session() -> Generator[Session, None, None]:
    with Session(get_engine()) as session:
        yield session


def create_all_models(engine=None) -> None:
    SQLModel.metadata.create_all(engine or get_engine())
