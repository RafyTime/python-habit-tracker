from typing import Annotated

import questionary
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from sqlmodel import Session, select
from typer import Argument, Exit, Option, Typer

from src.core.db import get_session
from src.core.models import AppState, Profile

cli = Typer()
console = Console()


def get_active_profile(session: Session) -> Profile | None:
    state = session.get(AppState, 1)
    if state and state.active_profile_id:
        return session.get(Profile, state.active_profile_id)
    return None


def set_active_profile(session: Session, profile_id: int) -> None:
    state = session.get(AppState, 1)
    if not state:
        state = AppState(id=1, active_profile_id=profile_id)
        session.add(state)
    else:
        state.active_profile_id = profile_id
        session.add(state)
    session.commit()


@cli.command()
def create(
    username: Annotated[str, Argument(help='The username to create')] = None,
):
    """Create a new user profile."""
    session: Session = next(get_session())

    print(Panel.fit('Create a New Profile', style='bold blue'))

    while True:
        if not username:
            username = Prompt.ask('Enter a username').strip()

        if not username:
            print('[red]Username cannot be empty.[/red]')
            username = None  # Reset so prompt asks again for username
            continue

        # Check if exists username already exists
        statement = select(Profile).where(Profile.username == username.lower())
        existing = session.exec(statement).first()

        if existing:
            print(
                f"[red]Profile '{username}' already exists. Please choose another.[/red]"
            )
            username = None  # Reset so prompt asks again for username
            continue

        break

    # Create profile
    # Storing username as lowercase for cli consistency
    profile = Profile(username=username.lower())
    session.add(profile)
    session.commit()
    session.refresh(profile)

    print(f"[green]Profile '{username}' created successfully![/green]")

    # Prompt to switch
    if Confirm.ask(f"Do you want to switch to '{username}' now?"):
        set_active_profile(session, profile.id)
        print(f"[green]Switched to profile '{username}'.[/green]")

    print('\n[bold]Next Steps:[/bold]')
    print(' - Create a habit: [cyan]habit create[/cyan]')
    print(' - List profiles: [cyan]profile list[/cyan]')


@cli.command('list')
def list_profiles():
    """List all available profiles."""
    session: Session = next(get_session())

    profiles = session.exec(select(Profile)).all()
    active_profile = get_active_profile(session)

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
    username: Annotated[str, Argument(help='The username to switch to')] = None,
):
    """Switch the active profile."""
    session: Session = next(get_session())

    if not username:
        # Interactive selection
        profiles = session.exec(select(Profile)).all()
        if not profiles:
            print(
                "[yellow]No profiles found. Create one with 'profile create'.[/yellow]"
            )
            raise Exit(1)

        active_profile = get_active_profile(session)
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

    profile = session.exec(
        select(Profile).where(Profile.username == username.lower())
    ).first()

    if not profile:
        print(f"[red]Profile '{username}' not found.[/red]")
        raise Exit(1)

    set_active_profile(session, profile.id)
    print(f"[green]Successfully switched to profile '{profile.username}'.[/green]")


@cli.command()
def me():
    """Show the current active profile."""
    session: Session = next(get_session())

    active_profile = get_active_profile(session)

    if not active_profile:
        print("[yellow]No active profile set. Use 'profile switch' to set one.[/yellow]")
        return

    print(f"[green]Active profile:[/green] {active_profile.username}")


@cli.command()
def delete(
    username: Annotated[str, Argument(help='The username to delete')] = None,
    force: Annotated[
        bool, Option('--force', '-f', help='Force delete without confirmation')
    ] = False,
):
    """Delete a user profile."""
    session: Session = next(get_session())

    if not username:
        # Interactive selection
        profiles = session.exec(select(Profile)).all()
        if not profiles:
            print('[yellow]No profiles found.[/yellow]')
            raise Exit(1)

        active_profile = get_active_profile(session)
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

    profile = session.exec(
        select(Profile).where(Profile.username == username.lower())
    ).first()

    if not profile:
        print(f"[red]Profile '{username}' not found.[/red]")
        raise Exit(1)

    active_profile = get_active_profile(session)
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

    # If deleting active profile, clear state
    if is_active:
        state = session.get(AppState, 1)
        if state:
            state.active_profile_id = None
            session.add(state)

    session.delete(profile)
    session.commit()

    print(f"[green]Profile '{username}' deleted.[/green]")
