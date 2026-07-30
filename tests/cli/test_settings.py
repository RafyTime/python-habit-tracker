from sqlmodel import Session, select
from typer.testing import CliRunner

from src.cli.settings import cli
from src.core.models import Profile
from src.core.profile import ProfileService

runner = CliRunner()


def test_settings_show_display_name(session: Session):
    """Fresh profile can be viewed through settings without account commands."""
    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['show'])
    assert result.exit_code == 0
    assert 'User' in result.stdout
    assert 'profile create' not in result.stdout
    assert 'profile switch' not in result.stdout


def test_settings_set_display_name(session: Session):
    """Users can change the single profile display name via settings."""
    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = runner.invoke(cli, ['name', 'Alex'])
    assert result.exit_code == 0
    assert 'Alex' in result.stdout

    profile = session.exec(select(Profile)).one()
    assert profile.username == 'Alex'

    show = runner.invoke(cli, ['show'])
    assert show.exit_code == 0
    assert 'Alex' in show.stdout
