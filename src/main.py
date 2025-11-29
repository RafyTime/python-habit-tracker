import time
from typing import Annotated

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from rich.table import Table
from typer import Exit, Option, Typer, prompt

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
def hello():
    """Say hello to a user"""
    name = prompt('What is your name?')
    print(f'[green]Hello {name}![/green]')


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


@app.command()
def progress():
    """Testing the progress bar functionality"""
    total = 0
    for _ in track(range(100), description='Processing...'):
        # Fake processing time
        time.sleep(0.1)
        total += 1
    print(f'Processed {total} things.')


@app.command()
def spinner():
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        transient=True,
    ) as progress:
        progress.add_task(description='Processing...', total=None)
        progress.add_task(description='Preparing...', total=None)
        time.sleep(5)
    print('Done!')


@app.command()
def error(name: str = 'morty'):
    print(name + 3)


if __name__ == '__main__':
    app()
