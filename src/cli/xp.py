from typing import Annotated

from typer import Option

from src.cli import render
from src.core.db import get_session
from src.core.habit.service import HabitService
from src.core.xp import XPService


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
        render.blank()
        render.stats(
            [
                ('Total', str(total_xp)),
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
            render.blank()
            render.heading('History')
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
                            habit_name or '-',
                        ]
                    )
                render.table(['When', 'XP', 'Why', 'Habit'], rows)
            else:
                render.warning('No XP events yet.')
        if total_xp == 0:
            render.blank()
            render.next_step('mark a habit done with [cyan]habit done[/cyan].')
