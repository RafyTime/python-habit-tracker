from typing import Annotated

from rich import print
from rich.console import Console
from rich.table import Table
from sqlmodel import select
from sqlmodel.sql.expression import desc
from typer import Context, Option, Typer

from src.cli import render
from src.core.db import get_session
from src.core.habit.service import HabitService
from src.core.models import XPEvent
from src.core.xp import XPService

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

    total_xp = service.get_total_xp_for_active_profile()
    level, xp_into_level, xp_to_next_level = (
        service.get_level_progress_for_active_profile()
    )

    print(f'[bold]Total XP:[/bold] {total_xp}')
    print(f'[bold]Level:[/bold] {level}')
    print(
        f'[bold]Progress:[/bold] {xp_into_level}/10 XP to next level ({xp_to_next_level} remaining)'
    )


@cli.command()
def log(
    ctx: Context,
    limit: Annotated[
        int, Option('--limit', '-l', help='Maximum number of events to show')
    ] = 10,
):
    """Show recent XP events."""
    service: XPService = ctx.obj.xp_service

    session = service._get_session()
    profile = service._get_active_profile(session)

    statement = (
        select(XPEvent)
        .where(XPEvent.profile_id == profile.id)
        .order_by(desc(XPEvent.awarded_at))
        .limit(limit)
    )
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


def _reason_label(reason: str) -> str:
    if reason == 'HABIT_COMPLETION':
        return 'Completion'
    if reason.startswith('MILESTONE_STREAK_'):
        return 'Milestone'
    return reason


def show_xp(
    history: Annotated[bool, Option('--history', help='Show recent XP events')] = False,
    limit: Annotated[
        int, Option('--limit', '-n', help='Maximum number of XP events to show')
    ] = 10,
) -> None:
    """Show XP, level, and progress to the next level."""
    service = XPService(get_session)
    total_xp = service.get_total_xp_for_active_profile()
    level, xp_into_level, xp_to_next_level = (
        service.get_level_progress_for_active_profile()
    )
    xp_for_level = xp_into_level + xp_to_next_level
    with render.view():
        render.heading('XP')
        render.stats(
            [
                ('XP', str(total_xp)),
                ('Level', str(level)),
            ]
        )
        render.progress(
            'Progress',
            f'{xp_into_level}/{xp_for_level} XP',
            completed=xp_into_level,
            total=xp_for_level,
        )
        if history:
            events = service.list_recent_events_for_active_profile(limit)
            if events:
                habits = HabitService(get_session).list_habits(active_only=False)
                names = {habit.id: habit.name for habit in habits}
                rows = []
                for event in events:
                    habit_name = names.get(event.habit_id, '') if event.habit_id else ''
                    rows.append(
                        [
                            event.awarded_at.strftime('%Y-%m-%d'),
                            f'+{event.amount}',
                            _reason_label(event.reason),
                            habit_name or '—',
                        ]
                    )
                render.blank()
                render.table(['When', 'XP', 'Why', 'Habit'], rows)
            else:
                render.warning('No XP events yet.')
        if total_xp == 0:
            render.next_step('mark a habit done with [cyan]habit done[/cyan].')
