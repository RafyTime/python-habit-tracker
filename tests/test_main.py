from typer.testing import CliRunner

from main import app


def test_app_exists():
    """Test that the app exists and is a Typer instance."""
    assert app is not None
    assert hasattr(app, 'command')


def test_app_help():
    """Test that the help command works and shows the run command."""
    runner = CliRunner()
    result = runner.invoke(app, ['--help'])
    assert result.exit_code == 0
    assert 'run' in result.stdout
