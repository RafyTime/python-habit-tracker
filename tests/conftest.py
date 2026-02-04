from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine

from src.core.models import AppState, Profile


@pytest.fixture(name="session")
def session_fixture() -> Generator[Session]:
    """
    Creates an in-memory SQLite database and yields a session.
    """
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(autouse=True)
def mock_get_session(session: Session):
    """
    Patches the get_session function in CLI modules to return the test session.
    """
    # Use side_effect to return a new iterator each time get_session is called
    with patch("src.cli.profile.get_session", side_effect=lambda: iter([session])), patch(
        "src.cli.habit.get_session", side_effect=lambda: iter([session])
    ), patch(
        "src.cli.xp.get_session", side_effect=lambda: iter([session])
    ), patch(
        "src.cli.overview.get_session", side_effect=lambda: iter([session])
    ):
        yield


@pytest.fixture(name="active_profile")
def active_profile_fixture(session: Session) -> Profile:
    """
    Creates a profile and sets it as the active profile in AppState.
    
    This fixture properly handles the commit order to ensure profile.id is available
    before setting active_profile_id in AppState.
    """
    profile = Profile(username="testuser")
    session.add(profile)
    session.commit()
    session.refresh(profile)
    
    # Now that profile.id is set, create/update AppState
    app_state = AppState(id=1, active_profile_id=profile.id)
    session.add(app_state)
    session.commit()
    
    return profile

