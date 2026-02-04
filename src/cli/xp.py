from typing import Annotated

from rich import print
from rich.console import Console
from rich.table import Table
from typer import Context, Exit, Option, Typer

from src.core.db import get_session
from src.core.habit.service import HabitService
from src.core.models import Habit
from src.core.xp import ActiveProfileRequired, XPService
from sqlmodel import select

cli = Typer()
console = Console()


class XPCLIContext:
    """Context object for XP CLI commands."""

    def __init__(self) -> None:
        self.xp_service = XPService(get_session)


@cli.callback()
def xp_callback(ctx: Context) -> None:
    """Initialize XP service in context."""
    ctx.obj = XPCLIContext()


@cli.command()
def status(ctx: Context):
    """Show XP status: total XP, level, and progress to next level."""
    service: XPService = ctx.obj.xp_service

    try:
        total_xp = service.get_total_xp_for_active_profile()
        level, xp_into_level, xp_to_next_level = service.get_level_progress_for_active_profile()

        print(f"[bold]Total XP:[/bold] {total_xp}")
        print(f"[bold]Level:[/bold] {level}")
        print(f"[bold]Progress:[/bold] {xp_into_level}/10 XP to next level ({xp_to_next_level} remaining)")

    except ActiveProfileRequired:
        print('[red]No active profile. Use "profile switch" to set an active profile.[/red]')
        raise Exit(1)


@cli.command()
def log(
    ctx: Context,
    limit: Annotated[
        int, Option('--limit', '-l', help='Maximum number of events to show')
    ] = 10,
):
    """Show recent XP events."""
    service: XPService = ctx.obj.xp_service

    try:
        session = service._get_session()
        profile = service._get_active_profile(session)

        from src.core.models import XPEvent
        statement = select(XPEvent).where(
            XPEvent.profile_id == profile.id
        ).order_by(XPEvent.awarded_at.desc()).limit(limit)
        events = list(session.exec(statement))

        if not events:
            print('[yellow]No XP events found.[/yellow]')
            return

        # Get habit names for display
        habit_service = HabitService(get_session)
        all_habits = habit_service.list_habits(active_only=False)
        habit_map = {h.id: h.name for h in all_habits}

        table = Table(title='Recent XP Events')
        table.add_column('Date', justify='right', style='cyan')
        table.add_column('Amount', justify='right', style='green')
        table.add_column('Reason', style='magenta')
        table.add_column('Habit', style='yellow')

        for event in events:
            habit_name = habit_map.get(event.habit_id, 'N/A') if event.habit_id else 'N/A'
            table.add_row(
                event.awarded_at.strftime('%Y-%m-%d %H:%M'),
                f'+{event.amount}',
                event.reason,
                habit_name,
            )

        console.print(table)

    except ActiveProfileRequired:
        print('[red]No active profile. Use "profile switch" to set an active profile.[/red]')
        raise Exit(1)
