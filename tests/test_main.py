from typer.testing import CliRunner

from main import app

runner = CliRunner()


def test_app_exists():
    """Test that the app exists and is a Typer instance."""
    assert app is not None
    assert hasattr(app, 'command')


def test_app_help():
    """Test that help lists settings and habit commands, not profile account management."""
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'settings' in result.stdout
    assert 'habit' in result.stdout
    assert 'xp' in result.stdout
    assert 'overview' in result.stdout
    assert 'seed' in result.stdout
    assert 'Manage user profiles' not in result.stdout
    assert 'profile create' not in result.stdout
    assert 'profile switch' not in result.stdout
