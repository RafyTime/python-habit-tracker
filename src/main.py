from typing import Annotated

from rich import print
from typer import Context, Exit, Option, Typer

from src.cli.analytics import stats as stats_command
from src.cli.habit import add as add_command
from src.cli.habit import archive_habit as archive_command
from src.cli.habit import delete_habit as delete_command
from src.cli.habit import done as done_command
from src.cli.habit import edit as edit_command
from src.cli.habit import restore as restore_command
from src.cli.habit import show_habits as list_command
from src.cli.home import home
from src.cli.home import today as today_command
from src.cli.seed import seed as seed_command
from src.cli.settings import settings as settings_command
from src.cli.start import start as start_command
from src.cli.xp import show_xp as xp_command
from src.core.config import app_settings
from src.core.db import init_db

_EVERYDAY = 'Everyday'
_PROGRESS = 'Progress'
_MANAGE = 'Manage'
_GET_STARTED = 'Get started and evaluate'

app = Typer(
    rich_markup_mode='rich',
    suggest_commands=True,
    help=f'{app_settings.PROJECT_NAME} - {app_settings.PROJECT_DESCRIPTION}',
    epilog=f'Version: {app_settings.PROJECT_VERSION}',
)


def version_callback(value: bool) -> bool:
    if value:
        print(f'[bold green]v{app_settings.PROJECT_VERSION}[/bold green]')
        raise Exit()
    return value


@app.callback(invoke_without_command=True)
def main(
    ctx: Context,
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
    if ctx.invoked_subcommand is not None:
        return
    home()


app.command(rich_help_panel=_EVERYDAY)(today_command)
app.command(rich_help_panel=_EVERYDAY)(add_command)
app.command(rich_help_panel=_EVERYDAY)(done_command)
app.command(name='list', rich_help_panel=_EVERYDAY)(list_command)
app.command(rich_help_panel=_PROGRESS)(stats_command)
app.command(name='xp', rich_help_panel=_PROGRESS)(xp_command)
app.command(rich_help_panel=_MANAGE)(edit_command)
app.command(name='archive', rich_help_panel=_MANAGE)(archive_command)
app.command(rich_help_panel=_MANAGE)(restore_command)
app.command(name='delete', rich_help_panel=_MANAGE)(delete_command)
app.command(rich_help_panel=_MANAGE)(settings_command)
app.command(rich_help_panel=_GET_STARTED)(start_command)
app.command(rich_help_panel=_GET_STARTED)(seed_command)


if __name__ == '__main__':
    app()
