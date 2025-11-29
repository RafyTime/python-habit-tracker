from typing import Annotated

from rich import print
from typer import Option, Typer

cli = Typer(
    help='Users management commands',
)


@cli.command()
def register(
    username: Annotated[str, Option(prompt=True, help='The username to register')],
    password: Annotated[
        str,
        Option(
            prompt=True,
            confirmation_prompt='Confirm password',
            hide_input=True,
            help='The password to register',
        ),
    ],
):
    """Register a new user"""
    print(f'[green]Registering a new user {username} with password {password}[/green]')


@cli.command()
def login(
    username: Annotated[str, Option(prompt=True, help='The username to login')],
    password: Annotated[
        str,
        Option(
            prompt=True,
            hide_input=True,
            help='The password to login',
        ),
    ],
    remember: Annotated[
        bool, Option(prompt=True, help='Save the login credentials?')
    ] = False,
):
    """Login a user"""
    print(f'[cyan]Logging in a user {username} with password {password}[/cyan]')
    if remember:
        print(f'[cyan]Saving the login credentials for {username}[/cyan]')


@cli.command()
def logout(
    username: Annotated[str, Option(prompt=True, help='The username to logout')],
):
    """Logout a user"""
    print(f'[red]Logging out a user {username}[/red]')
