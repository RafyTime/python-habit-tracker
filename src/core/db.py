from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from .config import app_settings
from .models import Item  # noqa: F401 - Import to register models with SQLModel

engine = create_engine(app_settings.DATABASE_URL, echo=app_settings.DEBUG)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
