"""CLI tests for the one persisted profile."""

from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.core.models import Profile
from src.core.profile import ProfileService

runner = CliRunner()


def _invoke(args: list[str]):
    with patch('main.init_db'):
        return runner.invoke(app, args)


def test_fresh_startup_ensures_usable_profile(session: Session):
    """A fresh database gets one automatic profile without account commands."""
    service = ProfileService(lambda: iter([session]))
    profile = service.ensure_single_profile()

    assert profile.display_name == 'User'
    assert session.exec(select(Profile)).all() == [profile]

    result = _invoke(['settings'])
    assert result.exit_code == 0
    assert 'Display name' in result.stdout
    assert 'User' in result.stdout
    assert 'profile create' not in result.stdout
    assert 'profile switch' not in result.stdout


def test_settings_show_uses_existing_profile(session: Session):
    """Settings shows the existing display name without creating another profile."""
    profile = Profile(display_name='Alex')
    session.add(profile)
    session.commit()

    result = _invoke(['settings'])
    assert result.exit_code == 0
    assert 'Alex' in result.stdout
    assert len(session.exec(select(Profile)).all()) == 1
