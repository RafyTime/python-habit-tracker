import re
import tomllib
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from main import app
from src.core.config import app_settings

_ANSI = re.compile(r'\x1b\[[0-9;]*m')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()

PUBLIC_COMMANDS = (
    'start',
    'today',
    'add',
    'done',
    'list',
    'edit',
    'archive',
    'restore',
    'delete',
    'stats',
    'xp',
    'settings',
    'seed',
)
COMMAND_PANELS = {
    'today': 'Everyday',
    'add': 'Everyday',
    'done': 'Everyday',
    'list': 'Everyday',
    'stats': 'Progress',
    'xp': 'Progress',
    'edit': 'Manage',
    'archive': 'Manage',
    'restore': 'Manage',
    'delete': 'Manage',
    'settings': 'Manage',
    'start': 'Get started and evaluate',
    'seed': 'Get started and evaluate',
}
COMMAND_OPTIONS = {
    'add': ('--every', '-e', '--icon', '-i'),
    'list': ('--archived', '-a', '--every', '-e'),
    'edit': ('--name', '-n', '--icon', '-i', '--clear-icon', '--archived'),
    'archive': ('--force', '-f'),
    'delete': ('--force', '-f'),
    'stats': ('--archived', '-a'),
    'xp': ('--history', '--limit', '-n'),
    'settings': ('--name', '-n', '--after-action'),
    'seed': ('--at', '--force', '-f'),
}
LEGACY_PATHS = (
    ['habit', 'list'],
    ['habit', 'create'],
    ['habit', 'complete'],
    ['habit', 'due'],
    ['overview', 'daily'],
    ['analytics', 'habits'],
    ['analytics', 'longest'],
    ['xp', 'status'],
    ['xp', 'log'],
    ['settings', 'show'],
    ['settings', 'name'],
)


def _command_name(info) -> str:
    return info.name or info.callback.__name__


def _help_text(args: list[str] | None = None) -> str:
    with patch('main.init_db'):
        result = runner.invoke(app, args or ['--help'])
    assert result.exit_code == 0, result.output
    return _ANSI.sub('', result.stdout)


def test_app_exists():
    """Test that the app exists and is a Typer instance."""
    assert app is not None
    assert hasattr(app, 'command')


def test_habit_is_the_only_installed_executable() -> None:
    with (PROJECT_ROOT / 'pyproject.toml').open('rb') as pyproject_file:
        scripts = tomllib.load(pyproject_file)['project']['scripts']

    assert scripts == {'habit': 'src.main:app'}


def test_registered_commands_match_the_approved_contract() -> None:
    names = {_command_name(info) for info in app.registered_commands}
    panels = {
        _command_name(info): info.rich_help_panel for info in app.registered_commands
    }

    assert names == set(PUBLIC_COMMANDS)
    assert app.registered_groups == []
    assert panels == COMMAND_PANELS


def test_help_lists_flat_commands_in_purpose_groups() -> None:
    help_text = _help_text()

    for panel in COMMAND_PANELS.values():
        assert panel in help_text
    assert 'Welcome a new user' in help_text
    assert 'Manage user profiles' not in help_text
    assert 'profile create' not in help_text
    assert 'profile switch' not in help_text


def test_long_and_short_options_match_the_approved_contract() -> None:
    add_help = _help_text(['add', '--help'])
    for alias in ('day', 'daily', 'week', 'weekly'):
        assert alias in add_help

    for command, options in COMMAND_OPTIONS.items():
        help_text = _help_text([command, '--help'])
        for option in options:
            assert option in help_text, f'{command} missing {option}'


def test_legacy_command_groups_are_gone() -> None:
    help_text = _help_text()

    assert 'overview' not in help_text
    assert 'analytics' not in help_text
    assert '--interactive' not in help_text

    for path in LEGACY_PATHS:
        with patch('main.init_db'):
            result = runner.invoke(app, path)
        assert result.exit_code != 0, path


def test_confirmation_bypass_is_force_not_yes() -> None:
    for command in ('archive', 'delete', 'seed'):
        help_text = _help_text([command, '--help'])
        assert '--force' in help_text
        assert '-f' in help_text
        assert '--yes' not in help_text


def test_version_is_available_as_an_eager_root_option() -> None:
    help_text = _help_text()
    assert '--version' in help_text
    assert '-V' in help_text

    result = runner.invoke(app, ['--version'])
    assert result.exit_code == 0
    assert app_settings.PROJECT_VERSION in _ANSI.sub('', result.stdout)
    assert 'Traceback' not in result.output
