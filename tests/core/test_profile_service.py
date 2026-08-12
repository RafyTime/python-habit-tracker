from collections.abc import Iterator

from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from src.core.models import AppState, Profile
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


def test_ensure_single_profile_username_readable_after_session_closes():
    """Returned profile stays readable after the producing session closes."""
    engine = _memory_engine()
    service = ProfileService(_closing_session_factory(engine))

    profile = service.ensure_single_profile()

    assert profile.username == 'User'


def test_existing_profile_username_readable_after_session_closes():
    """An already-persisted profile stays readable after ensure commits."""
    engine = _memory_engine()
    with Session(engine) as session:
        profile = Profile(username='Alex')
        session.add(profile)
        session.commit()
        session.refresh(profile)
        session.add(AppState(id=1, active_profile_id=profile.id))
        session.commit()

    service = ProfileService(_closing_session_factory(engine))
    ensured = service.ensure_single_profile()

    assert ensured.username == 'Alex'
