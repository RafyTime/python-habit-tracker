from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.profile import cli
from src.core.models import ActiveSession, Profile

runner = CliRunner()

def test_create_profile(session: Session):
    result = runner.invoke(cli, ["create", "testuser"], input="n\n")
    assert result.exit_code == 0
    assert "Profile 'testuser' created successfully!" in result.stdout

    # Verify in DB
    profile = session.exec(select(Profile).where(Profile.username == "testuser")).first()
    assert profile is not None
    assert profile.username == "testuser"

def test_create_profile_interactive(session: Session):
    # Simulate entering "testuser2" at the prompt
    result = runner.invoke(cli, ["create"], input="testuser2\nn\n") # username then 'n' for switch confirmation
    assert result.exit_code == 0
    assert "Profile 'testuser2' created successfully!" in result.stdout

    # Verify in DB
    profile = session.exec(select(Profile).where(Profile.username == "testuser2")).first()
    assert profile is not None

def test_create_existing_profile(session: Session):
    # Create first
    session.add(Profile(username="existing"))
    session.commit()

    # We patch Prompt.ask to return "newuser" when called
    # We still provide input="n\n" for the Confirm.ask at the end
    with patch("src.cli.profile.Prompt.ask", return_value="newuser"):
        result = runner.invoke(cli, ["create", "existing"], input="n\n")

    assert "Profile 'existing' already exists" in result.stdout
    assert "Profile 'newuser' created successfully" in result.stdout

    profile = session.exec(select(Profile).where(Profile.username == "newuser")).first()
    assert profile is not None

def test_list_profiles_empty(session: Session):
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "No profiles found" in result.stdout

def test_list_profiles(session: Session):
    session.add(Profile(username="user1"))
    session.add(Profile(username="user2"))
    session.commit()

    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "user1" in result.stdout
    assert "user2" in result.stdout

def test_switch_profile(session: Session):
    p1 = Profile(username="user1")
    session.add(p1)
    session.commit()

    result = runner.invoke(cli, ["switch", "user1"])
    assert result.exit_code == 0
    assert "Successfully switched to profile 'user1'" in result.stdout

    # Verify active session
    active_session = session.get(ActiveSession, 1)
    assert active_session is not None
    assert active_session.active_profile_id == p1.id

def test_switch_profile_not_found(session: Session):
    result = runner.invoke(cli, ["switch", "nonexistent"])
    assert result.exit_code == 1
    assert "Profile 'nonexistent' not found" in result.stdout

def test_delete_profile(session: Session):
    p1 = Profile(username="todelete")
    session.add(p1)
    session.commit()

    # Confirm deletion with 'y'
    result = runner.invoke(cli, ["delete", "todelete"], input="y\n")
    assert result.exit_code == 0
    assert "Profile 'todelete' deleted" in result.stdout

    # Verify deleted
    p = session.exec(select(Profile).where(Profile.username == "todelete")).first()
    assert p is None

def test_delete_active_profile(session: Session):
    p1 = Profile(username="active")
    session.add(p1)
    session.commit()

    # Set as active
    session.add(ActiveSession(id=1, active_profile_id=p1.id))
    session.commit()

    result = runner.invoke(cli, ["delete", "active"], input="y\n")
    assert result.exit_code == 0
    assert "Warning: 'active' is the currently active profile" in result.stdout
    assert "Profile 'active' deleted" in result.stdout

    # Verify active session cleared
    active_session = session.get(ActiveSession, 1)
    assert active_session.active_profile_id is None

def test_delete_profile_force(session: Session):
    p1 = Profile(username="force")
    session.add(p1)
    session.commit()

    result = runner.invoke(cli, ["delete", "force", "--force"])
    assert result.exit_code == 0
    assert "Profile 'force' deleted" in result.stdout

    p = session.exec(select(Profile).where(Profile.username == "force")).first()
    assert p is None
