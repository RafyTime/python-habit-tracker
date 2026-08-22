from typing import Annotated

from rich import print
from typer import Exit, Option, Typer

from src.cli.analytics import cli as analytics_cli
from src.cli.habit import add as add_command
from src.cli.habit import cli as habit_cli
from src.cli.habit import show_habits as list_command
from src.cli.home import today as today_command
from src.cli.overview import cli as overview_cli
from src.cli.seed import seed as seed_command
from src.cli.settings import cli as settings_cli
from src.cli.xp import cli as xp_cli
from src.core.config import app_settings
from src.core.db import init_db

app = Typer(
    no_args_is_help=True,
    rich_markup_mode='rich',
    suggest_commands=True,
    help=f'{app_settings.PROJECT_NAME} - {app_settings.PROJECT_DESCRIPTION}',
    epilog=f'Version: {app_settings.PROJECT_VERSION}',
)
app.add_typer(habit_cli, name='habit', help='Manage habits')
app.add_typer(settings_cli, name='settings', help='View and update profile settings')
app.add_typer(xp_cli, name='xp', help='XP and level progress')
app.add_typer(overview_cli, name='overview', help='Daily snapshot')
app.add_typer(analytics_cli, name='analytics', help='Analytics')


def version_callback(value: bool) -> bool:
    if value:
        print(f'[bold green]v{app_settings.PROJECT_VERSION}[/bold green]')
        raise Exit()
    return value


@app.callback()
def main(
    version: Annotated[
        bool | None,
        Option(
            '--version',
            '-V',
            help='Display the program version',
            is_eager=True,
            callback=version_callback,
        ),
    ] = None,
):
    _ = version
    init_db()


app.command()(today_command)
app.command()(add_command)
app.command(name='list')(list_command)
app.command()(seed_command)


if __name__ == '__main__':
    app()
