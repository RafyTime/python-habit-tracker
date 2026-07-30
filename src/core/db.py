from collections.abc import Generator

from sqlmodel import Session, create_engine

from . import models as _models
from .config import app_settings

engine = create_engine(app_settings.DATABASE_URL, echo=app_settings.DEBUG)


def init_db() -> None:
    _models.SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
