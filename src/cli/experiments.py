import time
from typing import Annotated

from rich import print
from rich.progress import Progress, SpinnerColumn, TextColumn, track
from rich.table import Table
from typer import Option, Typer, prompt

cli = Typer(
    help='Experiments commands',
)


@cli.command()
def hello():
    """Say hello to a user"""
    name = prompt('What is your name?')
    print(f'[green]Hello {name}![/green]')


@cli.command()
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


@cli.command()
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


@cli.command()
def progress():
    """Testing the progress bar functionality"""
    total = 0
    for _ in track(range(100), description='Processing...'):
        # Fake processing time
        time.sleep(0.1)
        total += 1
    print(f'Processed {total} things.')


@cli.command()
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


@cli.command()
def error(name: str = 'morty'):
    print(name + 3)
