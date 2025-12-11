from collections.abc import Generator
from unittest.mock import patch

import pytest
from sqlmodel import Session, SQLModel, create_engine


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
    Patches the get_session function in src.cli.profile to return the test session.
    """
    # Use side_effect to return a new iterator each time get_session is called
    with patch("src.cli.profile.get_session", side_effect=lambda: iter([session])):
        yield

