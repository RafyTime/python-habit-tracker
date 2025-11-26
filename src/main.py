from rich import print
from rich.table import Table
from typer import Argument, Exit, Option, Typer

from src.core.config import app_settings

app = Typer()


@app.command()
def run():
    print(
        f'✨ [cyan]Hello from {app_settings.PROJECT_NAME}! v{app_settings.PROJECT_VERSION}[/cyan] 🚀'
    )


@app.command()
def hello(
    name: str = Argument(help='The name to say hello to'),
    formal: bool = Option(default=False, help='Whether to use formal greeting'),
):
    if formal:
        print(f'Greetings, {name}! 🧐')
        raise Exit()
    print(f'Hello {name}! 😁')


@app.command()
def table():
    # Just a command to test the table functionality
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
