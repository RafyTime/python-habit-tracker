from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Context, Typer

from src.core.db import get_session
from src.core.habit.service import HabitService
from src.core.profile import ProfileService
from src.core.xp import XPService

cli = Typer()
console = Console()


class OverviewCLIContext:
    """Context object for overview CLI commands."""

    def __init__(self) -> None:
        self.profile_service = ProfileService(get_session)
        self.habit_service = HabitService(get_session)
        self.xp_service = XPService(get_session)


@cli.callback()
def overview_callback(ctx: Context) -> None:
    """Initialize services in context."""
    ctx.obj = OverviewCLIContext()


@cli.command()
def daily(ctx: Context):
    """Show daily snapshot: active profile, due habits, and XP summary."""
    profile_service: ProfileService = ctx.obj.profile_service
    habit_service: HabitService = ctx.obj.habit_service
    xp_service: XPService = ctx.obj.xp_service

    # Get active profile
    active_profile = profile_service.get_active_profile()

    if not active_profile:
        print('[yellow]No active profile set. Use "profile switch" to set one.[/yellow]')
        print('[dim]Tip: Create a profile with "profile create" if you don\'t have one.[/dim]')
        return

    print(Panel.fit(f'Daily Overview - {active_profile.username}', style='bold blue'))

    # Show due habits
    try:
        due_habits = habit_service.get_due_habits()

        if not due_habits:
            print('[green]All habits are completed for this period! Great job! 🎉[/green]')
        else:
            table = Table(title='Due Habits', show_header=True, header_style='bold magenta')
            table.add_column('ID', justify='right', style='cyan', no_wrap=True)
            table.add_column('Name', style='magenta')
            table.add_column('Periodicity', justify='center')

            for habit in due_habits:
                table.add_row(
                    str(habit.id),
                    habit.name,
                    habit.periodicity.value,
                )

            console.print(table)
            print()

    except Exception:
        # If there's an error (e.g., ActiveProfileRequired), skip due habits
        pass

    # Show XP summary
    try:
        total_xp = xp_service.get_total_xp_for_active_profile()
        level, xp_into_level, xp_to_next_level = xp_service.get_level_progress_for_active_profile()

        print(f"[bold]XP Summary:[/bold]")
        print(f"  Total XP: {total_xp}")
        print(f"  Level: {level}")
        print(f"  Progress: {xp_into_level}/10 XP to next level ({xp_to_next_level} remaining)")
    except Exception:
        # If there's an error, skip XP summary
        pass
