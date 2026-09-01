from typing import Annotated

from rich import print
from typer import Context, Exit, Option, Typer

from src.cli.analytics import cli as analytics_cli
from src.cli.analytics import stats as stats_command
from src.cli.habit import add as add_command
from src.cli.habit import archive_habit as archive_command
from src.cli.habit import cli as habit_cli
from src.cli.habit import delete_habit as delete_command
from src.cli.habit import done as done_command
from src.cli.habit import edit as edit_command
from src.cli.habit import restore as restore_command
from src.cli.habit import show_habits as list_command
from src.cli.home import home
from src.cli.home import today as today_command
from src.cli.overview import cli as overview_cli
from src.cli.seed import seed as seed_command
from src.cli.settings import cli as settings_cli
from src.cli.start import start as start_command
from src.cli.xp import show_xp as xp_command
from src.core.config import app_settings
from src.core.db import init_db

app = Typer(
    rich_markup_mode='rich',
    suggest_commands=True,
    help=f'{app_settings.PROJECT_NAME} - {app_settings.PROJECT_DESCRIPTION}',
    epilog=f'Version: {app_settings.PROJECT_VERSION}',
)
app.add_typer(habit_cli, name='habit', help='Manage habits')
app.add_typer(settings_cli, name='settings', help='View and update profile settings')
app.add_typer(overview_cli, name='overview', help='Daily snapshot')
app.add_typer(analytics_cli, name='analytics', help='Analytics')


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
    interactive: Annotated[
        bool,
        Option(
            '--interactive',
            help='Open the interactive home screen',
        ),
    ] = False,
):
    _ = version
    if ctx.invoked_subcommand is not None:
        init_db()
        return
    if interactive:
        init_db()
        home()
        return
    print(ctx.get_help())
    raise Exit()


app.command()(start_command)
app.command()(today_command)
app.command()(add_command)
app.command()(done_command)
app.command(name='list')(list_command)
app.command()(edit_command)
app.command(name='archive')(archive_command)
app.command()(restore_command)
app.command(name='delete')(delete_command)
app.command()(stats_command)
app.command(name='xp')(xp_command)
app.command()(seed_command)


if __name__ == '__main__':
    app()
