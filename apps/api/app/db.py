from sqlmodel import SQLModel, create_engine


def get_engine(url: str, **kwargs: object):
    return create_engine(url, future=True, **kwargs)


def create_all_models(engine) -> None:
    SQLModel.metadata.create_all(engine)
