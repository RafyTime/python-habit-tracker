from collections.abc import Generator, Iterator

from sqlmodel import Session, create_engine

from . import models as _models
from .config import app_settings

engine = create_engine(app_settings.DATABASE_URL, echo=app_settings.DEBUG)


def init_db() -> None:
    _models.SQLModel.metadata.create_all(engine)
    with Session(engine) as session:

        def session_factory() -> Iterator[Session]:
            return iter((session,))

        # Imported here to avoid circular imports during model metadata setup.
        from src.core.profile.service import ProfileService

        ProfileService(session_factory).ensure_single_profile()


def get_session() -> Generator[Session]:
    with Session(engine) as session:
        yield session
