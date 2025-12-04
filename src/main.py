from typing import Annotated

from rich import print
from typer import Exit, Option, Typer

from src.cli.experiments import cli as experiments_cli
from src.cli.items import cli as items_cli
from src.cli.users import cli as users_cli
from src.core.config import app_settings

app = Typer(
    no_args_is_help=True,
    rich_markup_mode='rich',
    suggest_commands=True,
    help=f'{app_settings.PROJECT_NAME} - {app_settings.PROJECT_DESCRIPTION}',
    epilog=f'Version: {app_settings.PROJECT_VERSION}',
)
app.add_typer(items_cli, name='items')
app.add_typer(users_cli, name='users')
app.add_typer(experiments_cli, name='x')


@app.callback()
def main(
    version: Annotated[
        bool | None,
        Option(
            '--version',
            '-v',
            help='Display the program version',
            is_eager=True,
        ),
    ] = None,
):
    if version:
        print(f'{app_settings.PROJECT_NAME} Version: {app_settings.PROJECT_VERSION}')
        raise Exit()


if __name__ == '__main__':
    app()
