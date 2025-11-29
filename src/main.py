from typing import Annotated

from rich import print
from rich.table import Table
from typer import Argument, Exit, Option, Typer

from src.core.config import app_settings

app = Typer(
    no_args_is_help=True,
    rich_markup_mode="rich",
    suggest_commands=True,
    help=f"{app_settings.PROJECT_NAME} - {app_settings.PROJECT_DESCRIPTION}",
    epilog=f"Version: {app_settings.PROJECT_VERSION}",
)


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

@app.command()
def truth(
    truth: Annotated[
        str,
        Option(
            prompt='Is it true?',
            confirmation_prompt='Is it really true?',
            help='The truth to test',
        ),
    ],
):
    """Testing the prompt & confirmation prompt & help functionality"""
    print(f'The truth is {truth}')


@app.command()
def register(
    username: Annotated[str, Argument(help='The username to register')],
    password: Annotated[
        str,
        Option(
            prompt=True,
            confirmation_prompt=True,
            hide_input=True,
            help='The password to register',
        ),
    ],
):
    """Testing the hide input & help functionality"""
    print(f'Hello {username}. Doing something very secure with password.')
    print(f'...just kidding, here it is, very insecure: {password}')


@app.command()
def table():
    """Testing the table functionality"""
    table = Table(title='Test Table')
    table.add_column('Name', justify='right', style='cyan', no_wrap=True)
    table.add_column('Age', justify='right', style='magenta')
    table.add_column('City', justify='left', style='green')
    table.add_row('John', '25', 'New York')
    table.add_row('Jane', '30', 'Los Angeles')
    table.add_row('Jim', '35', 'Chicago')
    print(table)


if __name__ == '__main__':
    app()
