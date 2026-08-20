"""Home and daily snapshot commands."""

from datetime import datetime

from src.cli import render
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import Periodicity
from src.core.profile import ProfileService
from src.core.xp import XPService


def _greeting(display_name: str) -> str:
    hour = datetime.now().hour
    if hour < 12:
        period = 'morning'
    elif hour < 17:
        period = 'afternoon'
    else:
        period = 'evening'
    return f'Good {period}, {display_name}'


def today() -> None:
    """Show a snapshot of habits due today and this week."""
    profile_service = ProfileService(get_session)
    habit_service = HabitService(get_session)
    xp_service = XPService(get_session)

    profile = profile_service.ensure_single_profile()
    active_habits = habit_service.list_habits(active_only=True)

    with render.view():
        render.heading(_greeting(profile.username))
        render.blank()

        if not active_habits:
            render.warning('No habits yet.')
            render.next_step('add one with [cyan]habit add[/cyan].')
            return

        due_habits = habit_service.get_due_habits()
        completed_count = len(active_habits) - len(due_habits)
        level, xp_into_level, xp_to_next_level = (
            xp_service.get_level_progress_for_active_profile()
        )
        render.stats(
            [
                (
                    'Today',
                    f'{render.bar(completed_count, len(active_habits))}  '
                    f'{completed_count} of {len(active_habits)} done',
                ),
                (
                    f'Level {level}',
                    f'[dim]{xp_into_level}/{xp_into_level + xp_to_next_level} XP[/dim]',
                ),
            ]
        )

        due_today = [
            habit for habit in due_habits if habit.periodicity == Periodicity.DAILY
        ]
        due_this_week = [
            habit for habit in due_habits if habit.periodicity == Periodicity.WEEKLY
        ]

        render.list_section('Due today', [habit.name for habit in due_today])
        render.list_section('Due this week', [habit.name for habit in due_this_week])

        if not due_habits:
            render.blank()
            render.success('All habits are done for now.')
