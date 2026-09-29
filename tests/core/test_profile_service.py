from collections.abc import Iterator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.core.models import Profile
from src.core.profile import ProfileService


def _memory_engine():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


def _closing_session_factory(engine):
    def session_factory() -> Iterator[Session]:
        with Session(engine) as session:
            yield session

    return session_factory


def test_ensure_single_profile_display_name_readable_after_session_closes():
    """Returned profile stays readable after the producing session closes."""
    engine = _memory_engine()
    service = ProfileService(_closing_session_factory(engine))

    profile = service.ensure_single_profile()

    assert profile.display_name == 'User'


def test_existing_profile_display_name_readable_after_session_closes():
    """An already-persisted profile stays readable after ensure commits."""
    engine = _memory_engine()
    with Session(engine) as session:
        profile = Profile(display_name='Alex')
        session.add(profile)
        session.commit()

    service = ProfileService(_closing_session_factory(engine))
    ensured = service.ensure_single_profile()

    assert ensured.display_name == 'Alex'
