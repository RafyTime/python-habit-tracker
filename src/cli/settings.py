from typing import Annotated

from rich import print
from rich.panel import Panel
from rich.prompt import Prompt
from typer import Argument, Context, Typer

from src.core.db import get_session
from src.core.profile import ProfileService

cli = Typer(help='View and update your profile settings')


class SettingsCLIContext:
    """Context object for settings CLI commands."""

    def __init__(self) -> None:
        self.profile_service = ProfileService(get_session)


@cli.callback(invoke_without_command=True)
def settings_callback(ctx: Context) -> None:
    """Initialize settings service; show settings when no subcommand is given."""
    ctx.obj = SettingsCLIContext()
    if ctx.invoked_subcommand is None:
        ctx.invoke(show)


@cli.command()
def show(ctx: Context) -> None:
    """Show the current profile settings."""
    service: ProfileService = ctx.obj.profile_service
    profile = service.ensure_single_profile()

    print(Panel.fit('Profile Settings', style='bold blue'))
    print(f'[green]Display name:[/green] {profile.username}')


@cli.command()
def name(
    ctx: Context,
    display_name: Annotated[
        str | None, Argument(help='The display name to set')
    ] = None,
) -> None:
    """Set the profile display name."""
    service: ProfileService = ctx.obj.profile_service
    service.ensure_single_profile()

    print(Panel.fit('Update Display Name', style='bold blue'))

    while True:
        if not display_name:
            display_name = Prompt.ask('Enter a display name').strip()

        if not display_name:
            print('[red]Display name cannot be empty.[/red]')
            display_name = None
            continue

        break

    profile = service.update_display_name(display_name)
    print(f"[green]Display name updated to '{profile.username}'.[/green]")

    print('\n[bold]Next Steps:[/bold]')
    print(' - Create a habit: [cyan]habit create[/cyan]')
    print(' - View daily overview: [cyan]overview daily[/cyan]')
