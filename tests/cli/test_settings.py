from unittest.mock import patch

from sqlmodel import Session, select
from typer.testing import CliRunner

from main import app
from src.cli.settings import cli
from src.core.models import AfterAction, Profile
from src.core.profile import ProfileService

runner = CliRunner()


def _invoke(args: list[str]):
    with patch('main.init_db'):
        return runner.invoke(app, args)


def test_settings_without_subcommand_shows_profile(session: Session):
    """cli settings with no subcommand shows the profile instead of crashing."""
    ProfileService(lambda: iter([session])).ensure_single_profile()

    result = _invoke(['settings'])
    assert result.exit_code == 0, result.output
    assert 'User' in result.stdout


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


def test_settings_shows_display_name_and_home_after_action(
    session: Session,
) -> None:
    result = _invoke(['settings'])

    assert result.exit_code == 0
    assert 'User' in result.stdout
    assert 'Display name' in result.stdout
    assert 'After an action' in result.stdout
    assert 'Return home' in result.stdout
    profile = session.exec(select(Profile)).one()
    assert profile.after_action == AfterAction.HOME


def test_settings_updates_name_and_after_action_without_prompts(
    session: Session,
) -> None:
    result = _invoke(['settings', '--name', 'Alex', '--after-action', 'exit'])

    assert result.exit_code == 0
    profile = session.exec(select(Profile)).one()
    assert profile.username == 'Alex'
    assert profile.after_action == AfterAction.EXIT
    assert 'Alex' in result.stdout
    assert 'Exit' in result.stdout

    shown = _invoke(['settings'])
    assert shown.exit_code == 0
    assert 'Alex' in shown.stdout
    assert 'Exit' in shown.stdout
    assert 'Return home' not in shown.stdout


def test_settings_rejects_unknown_after_action(session: Session) -> None:
    result = _invoke(['settings', '--after-action', 'bounce'])

    assert result.exit_code == 1
    assert 'home' in result.stdout.lower()
    assert 'exit' in result.stdout.lower()
    profile = session.exec(select(Profile)).one()
    assert profile.after_action == AfterAction.HOME


def test_non_interactive_settings_name_without_value_fails_with_an_example(
    session: Session,
) -> None:
    result = _invoke(['settings', 'name'])

    assert result.exit_code == 1
    assert 'habit settings --name' in result.stdout
    profile = session.exec(select(Profile)).one()
    assert profile.username == 'User'
