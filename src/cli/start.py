"""Quick start command."""

import sys

import questionary
from rich.prompt import Confirm, Prompt
from typer import Exit

from src.cli import render
from src.cli.habit import add, done
from src.cli.home import home
from src.cli.seed import seed
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import Habit, Periodicity
from src.core.profile import ProfileService

USER_GUIDE_URL = (
    'https://github.com/RafyTime/python-habit-tracker/blob/main/docs/USER_GUIDE.md'
)


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _ask_display_name(current: str) -> str:
    return Prompt.ask('What should we call you?', default=current).strip()


def _choose_beginning() -> str | None:
    return questionary.select(
        'How would you like to begin?',
        choices=[
            questionary.Choice(title='Create my first habit', value='personal'),
            questionary.Choice(title='Explore sample data', value='sample'),
        ],
    ).ask()


def _confirm_first_completion(habit: Habit) -> bool:
    period = 'today' if habit.periodicity == Periodicity.DAILY else 'this week'
    return Confirm.ask(f'Mark {habit.name} done for {period}?', default=True)


def start() -> None:
    """Welcome a new user and set up the first habit or sample data."""
    if not _can_prompt():
        render.error('Quick start needs an interactive terminal.')
        render.next_step(
            'run [cyan]habit start[/cyan] in a terminal, or add a habit with '
            '[cyan]habit add[/cyan].'
        )
        raise Exit(1)
    try:
        _run_start()
    except KeyboardInterrupt:
        raise Exit() from None


def _run_start() -> None:
    profile_service = ProfileService(get_session)
    habit_service = HabitService(get_session)
    profile = profile_service.ensure_single_profile()

    with render.view():
        render.heading('Quick start')
        render.note('A short tour of the main habit loop.')

    name = _ask_display_name(profile.username)
    if name:
        profile = profile_service.update_display_name(name)

    existing = habit_service.list_habits(active_only=False)
    if not existing:
        choice = _choose_beginning()
        if choice is None:
            raise Exit()
        if choice == 'sample':
            seed()
        elif choice == 'personal':
            add()
            _offer_first_completion(habit_service)

    _finish(profile.username)


def _offer_first_completion(habit_service: HabitService) -> None:
    habits = habit_service.list_habits(active_only=True)
    if len(habits) != 1:
        return
    habit = habits[0]
    if not _confirm_first_completion(habit):
        return
    done(habit.name)


def _finish(display_name: str) -> None:
    with render.view():
        render.success(f"You're ready, {display_name}.")
        render.note('Run [cyan]habit[/cyan] whenever you want to check in.')
        render.note('Full user guide:')
        render.note(USER_GUIDE_URL)
    home()
