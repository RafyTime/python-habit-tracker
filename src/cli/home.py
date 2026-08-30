"""Home and daily snapshot commands."""

import sys
from datetime import datetime

import questionary
from typer import Exit

from src.cli import render
from src.cli.analytics import stats
from src.cli.habit import add, done, show_habits
from src.cli.settings import edit_settings
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import AfterAction, Periodicity
from src.core.profile import ProfileService
from src.core.xp import XPService

_HOME_ACTIONS = (
    ('done', 'Mark a habit done', done),
    ('add', 'Add a habit', add),
    ('list', 'View habits', show_habits),
    ('stats', 'View stats', stats),
    ('settings', 'Settings', edit_settings),
    ('exit', 'Exit', None),
)


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _choose_action() -> str | None:
    return questionary.select(
        'What would you like to do?',
        choices=[
            questionary.Choice(title=label, value=value)
            for value, label, _handler in _HOME_ACTIONS
        ],
    ).unsafe_ask()


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

        render.list_section(
            'Due today',
            [render.labelled_habit(habit.name, habit.icon) for habit in due_today],
        )
        render.list_section(
            'Due this week',
            [render.labelled_habit(habit.name, habit.icon) for habit in due_this_week],
        )

        if not due_habits:
            render.blank()
            render.success('All habits are done for now.')


def home() -> None:
    """Open interactive home, or print the read-only today snapshot."""
    if not _can_prompt():
        today()
        return
    try:
        _run_home()
    except KeyboardInterrupt:
        raise Exit() from None


def _run_home() -> None:
    profile_service = ProfileService(get_session)
    handlers = {
        value: handler
        for value, _label, handler in _HOME_ACTIONS
        if handler is not None
    }
    while True:
        today()
        choice = _choose_action()
        if choice is None or choice == 'exit':
            return
        handler = handlers.get(choice)
        if handler is None:
            continue
        try:
            handler()
        except KeyboardInterrupt:
            raise Exit() from None
        except Exit as error:
            if error.exit_code in (0, None):
                continue
            profile = profile_service.ensure_single_profile()
            if profile.after_action == AfterAction.EXIT:
                raise
            continue
        profile = profile_service.ensure_single_profile()
        if profile.after_action == AfterAction.EXIT:
            return
