"""Home and daily snapshot commands."""

from datetime import datetime

from src.cli import presentation
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import Habit, Periodicity
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


def _print_due_section(title: str, habits: list[Habit]) -> None:
    if not habits:
        return
    presentation.heading(title)
    for habit in habits:
        presentation.console.print(habit.name)


def today() -> None:
    """Show a snapshot of habits due today and this week."""
    profile_service = ProfileService(get_session)
    habit_service = HabitService(get_session)
    xp_service = XPService(get_session)

    profile = profile_service.ensure_single_profile()
    active_habits = habit_service.list_habits(active_only=True)

    presentation.heading(_greeting(profile.username))

    if not active_habits:
        presentation.warning('No habits yet.')
        presentation.next_step('add one with `habit add`.')
        return

    due_habits = habit_service.get_due_habits()
    completed_count = len(active_habits) - len(due_habits)
    presentation.progress('Progress', f'{completed_count} of {len(active_habits)} done')

    level, xp_into_level, xp_to_next_level = (
        xp_service.get_level_progress_for_active_profile()
    )
    presentation.progress(
        f'Level {level}', f'{xp_into_level}/{xp_into_level + xp_to_next_level} XP'
    )

    due_today = [
        habit for habit in due_habits if habit.periodicity == Periodicity.DAILY
    ]
    due_this_week = [
        habit for habit in due_habits if habit.periodicity == Periodicity.WEEKLY
    ]

    _print_due_section('Due today', due_today)
    _print_due_section('Due this week', due_this_week)

    if not due_habits:
        presentation.success('All habits are done for now.')
