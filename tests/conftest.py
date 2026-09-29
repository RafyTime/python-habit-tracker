from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.core.models import Profile


@pytest.fixture(name='session')
def session_fixture() -> Generator[Session]:
    """
    Creates an in-memory SQLite database and yields a session.
    """
    engine = create_engine('sqlite:///:memory:')
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def mock_get_session(session: Session):
    """
    Patches the get_session function in CLI modules to return the test session.
    """
    # Use side_effect to return a new iterator each time get_session is called
    with (
        patch('src.cli.settings.get_session', side_effect=lambda: iter([session])),
        patch('src.cli.habit.get_session', side_effect=lambda: iter([session])),
        patch('src.cli.xp.get_session', side_effect=lambda: iter([session])),
        patch('src.cli.analytics.get_session', side_effect=lambda: iter([session])),
        patch('src.cli.seed.get_session', side_effect=lambda: iter([session])),
        patch('src.cli.start.get_session', side_effect=lambda: iter([session])),
        patch('src.core.db.get_session', side_effect=lambda: iter([session])),
    ):
        yield


@pytest.fixture(name='single_profile')
def single_profile_fixture(session: Session) -> Profile:
    """Create the tracker's profile for service tests."""
    profile = Profile(display_name='testuser')
    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile
