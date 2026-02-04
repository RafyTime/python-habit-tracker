from typing import Annotated

from rich import print
from typer import Exit, Option, Typer

from src.cli.habit import cli as habit_cli
from src.cli.profile import cli as profile_cli
from src.cli.xp import cli as xp_cli
from src.cli.overview import cli as overview_cli
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
app.add_typer(profile_cli, name='profile', help='Manage user profiles')
app.add_typer(xp_cli, name='xp', help='XP and level progress')
app.add_typer(overview_cli, name='overview', help='Daily snapshot')


def version_callback(value: bool) -> bool:
    if value:
        print(f'[bold green]v{app_settings.PROJECT_VERSION}[/bold green]')
        raise Exit()
    return value


@app.callback()
def main(
    version: Annotated[  # noqa: ARG001
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
    init_db()


if __name__ == '__main__':
    app()
