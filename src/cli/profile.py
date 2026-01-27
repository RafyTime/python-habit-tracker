from typing import Annotated

import questionary
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Context, Exit, Option, Typer

from src.core.db import get_session
from src.core.profile import ProfileAlreadyExists, ProfileNotFound, ProfileService

cli = Typer()
console = Console()


class ProfileCLIContext:
    """Context object for profile CLI commands."""

    def __init__(self) -> None:
        self.profile_service = ProfileService(get_session)


@cli.callback()
def profile_callback(ctx: Context) -> None:
    """Initialize profile service in context."""
    ctx.obj = ProfileCLIContext()


@cli.command()
def create(
    ctx: Context,
    username: Annotated[str, Argument(help='The username to create')] = None,
):
    """Create a new user profile."""
    service: ProfileService = ctx.obj.profile_service

    print(Panel.fit('Create a New Profile', style='bold blue'))

    while True:
        if not username:
            username = Prompt.ask('Enter a username').strip()

        if not username:
            print('[red]Username cannot be empty.[/red]')
            username = None  # Reset so prompt asks again for username
            continue

        try:
            service.create_profile(username)
            break
        except ProfileAlreadyExists:
            print(
                f"[red]Profile '{username}' already exists. Please choose another.[/red]"
            )
            username = None  # Reset so prompt asks again for username
            continue

    print(f"[green]Profile '{username}' created successfully![/green]")

    # Prompt to switch
    if Confirm.ask(f"Do you want to switch to '{username}' now?"):
        service.switch_active_profile(username)
        print(f"[green]Switched to profile '{username}'.[/green]")

    print('\n[bold]Next Steps:[/bold]')
    print(' - Create a habit: [cyan]habit create[/cyan]')
    print(' - List profiles: [cyan]profile list[/cyan]')


@cli.command('list')
def list_profiles(ctx: Context):
    """List all available profiles."""
    service: ProfileService = ctx.obj.profile_service

    profiles = service.list_profiles()
    active_profile = service.get_active_profile()

    if not profiles:
        print("[yellow]No profiles found. Create one with 'profile create'.[/yellow]")
        return

    table = Table(title='User Profiles')
    table.add_column('ID', justify='right', style='cyan', no_wrap=True)
    table.add_column('Username', style='magenta')
    table.add_column('Active', justify='center', style='green')
    table.add_column('Created At', justify='right')

    for profile in profiles:
        is_active = active_profile and active_profile.id == profile.id
        active_marker = '(*)' if is_active else ''
        table.add_row(
            str(profile.id),
            profile.username,
            active_marker,
            profile.created_at.strftime('%Y-%m-%d %H:%M'),
        )

    console.print(table)


@cli.command()
def switch(
    ctx: Context,
    username: Annotated[str, Argument(help='The username to switch to')] = None,
):
    """Switch the active profile."""
    service: ProfileService = ctx.obj.profile_service

    if not username:
        # Interactive selection
        profiles = service.list_profiles()
        if not profiles:
            print(
                "[yellow]No profiles found. Create one with 'profile create'.[/yellow]"
            )
            raise Exit(1)

        active_profile = service.get_active_profile()
        choices = []
        for p in profiles:
            is_active = active_profile and active_profile.id == p.id
            display_name = f'{p.username} (active)' if is_active else p.username
            choices.append(questionary.Choice(title=display_name, value=p.username))

        username = questionary.select(
            'Select profile to switch to:',
            choices=choices,
        ).ask()

        if not username:
            raise Exit()

    try:
        profile = service.switch_active_profile(username)
        print(f"[green]Successfully switched to profile '{profile.username}'.[/green]")
    except ProfileNotFound:
        print(f"[red]Profile '{username}' not found.[/red]")
        raise Exit(1)


@cli.command()
def me(ctx: Context):
    """Show the current active profile."""
    service: ProfileService = ctx.obj.profile_service

    active_profile = service.get_active_profile()

    if not active_profile:
        print(
            "[yellow]No active profile set. Use 'profile switch' to set one.[/yellow]"
        )
        return

    print(f'[green]Active profile:[/green] {active_profile.username}')


@cli.command()
def delete(
    ctx: Context,
    username: Annotated[str, Argument(help='The username to delete')] = None,
    force: Annotated[
        bool, Option('--force', '-f', help='Force delete without confirmation')
    ] = False,
):
    """Delete a user profile."""
    service: ProfileService = ctx.obj.profile_service

    if not username:
        # Interactive selection
        profiles = service.list_profiles()
        if not profiles:
            print('[yellow]No profiles found.[/yellow]')
            raise Exit(1)

        active_profile = service.get_active_profile()
        choices = []
        for p in profiles:
            is_active = active_profile and active_profile.id == p.id
            display_name = f'{p.username} (active)' if is_active else p.username
            choices.append(questionary.Choice(title=display_name, value=p.username))

        username = questionary.select(
            'Select profile to delete:',
            choices=choices,
        ).ask()

        if not username:
            raise Exit()

    # Check if profile exists and if it's active (for warning)
    try:
        active_profile = service.get_active_profile()
        profiles = service.list_profiles()
        profile = next((p for p in profiles if p.username == username.lower()), None)

        if not profile:
            print(f"[red]Profile '{username}' not found.[/red]")
            raise Exit(1)

        is_active = active_profile and active_profile.id == profile.id

        if is_active:
            print(
                f"[yellow]Warning: '{username}' is the currently active profile.[/yellow]"
            )

        if not force:
            if not Confirm.ask(
                f"Are you sure you want to delete profile '{username}'? All data will be lost."
            ):
                print('[yellow]Operation cancelled.[/yellow]')
                return

        service.delete_profile(username)
        print(f"[green]Profile '{username}' deleted.[/green]")
    except ProfileNotFound:
        print(f"[red]Profile '{username}' not found.[/red]")
        raise Exit(1)
