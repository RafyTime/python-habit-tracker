import re
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from main import app

_ANSI = re.compile(r'\x1b\[[0-9;]*m')

PROJECT_ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_app_exists():
    """Test that the app exists and is a Typer instance."""
    assert app is not None
    assert hasattr(app, 'command')


def test_habit_executable_is_exposed_without_removing_legacy_entry_points() -> None:
    with (PROJECT_ROOT / 'pyproject.toml').open('rb') as pyproject_file:
        scripts = tomllib.load(pyproject_file)['project']['scripts']

    assert scripts['habit'] == 'src.main:app'
    assert scripts['habits'] == 'src.main:app'
    assert scripts['app'] == 'src.main:app'
    assert scripts['cli'] == 'src.main:app'


def test_bare_habit_shows_help_without_opening_home() -> None:
    result = runner.invoke(app, [])
    help_text = _ANSI.sub('', result.stdout)

    assert result.exit_code == 0
    assert 'Usage' in help_text
    assert 'today' in help_text
    assert '--interactive' in help_text


def test_app_help():
    """Test that help lists settings and habit commands, not profile account management."""
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'settings' in result.stdout
    assert 'habit' in result.stdout
    assert 'xp' in result.stdout
    assert 'overview' in result.stdout
    assert 'seed' in result.stdout
    assert 'today' in result.stdout
    assert 'add' in result.stdout
    assert 'list' in result.stdout
    assert 'done' in result.stdout
    assert 'edit' in result.stdout
    assert 'archive' in result.stdout
    assert 'restore' in result.stdout
    assert 'delete' in result.stdout
    assert 'stats' in result.stdout
    assert 'Manage user profiles' not in result.stdout
    assert 'profile create' not in result.stdout
    assert 'profile switch' not in result.stdout
