"""Quick start command."""

import sys

import questionary
from rich.markup import escape
from rich.prompt import Confirm, Prompt
from typer import Exit

from src.cli import render
from src.cli.analytics import stats
from src.cli.habit import add, done
from src.cli.home import home, today
from src.cli.seed import seed
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import Habit, Periodicity
from src.core.profile import ProfileService

_QUICK_START_ICON = '▶️'
USER_GUIDE_URL = (
    'https://github.com/RafyTime/python-habit-tracker/blob/main/docs/USER_GUIDE.md'
)


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _ask_display_name(current: str) -> str:
    render.before_prompts()
    return Prompt.ask('What should we call you?', default=current).strip()


def _choose_beginning() -> str | None:
    render.before_prompts()
    return questionary.select(
        'How would you like to begin?',
        choices=[
            questionary.Choice(title='Create my first habit', value='personal'),
            questionary.Choice(title='Explore sample data', value='sample'),
        ],
        style=render.select_style,
    ).ask()


def _confirm_first_completion(habit: Habit) -> bool:
    period = 'today' if habit.periodicity == Periodicity.DAILY else 'this week'
    render.before_prompts()
    return Confirm.ask(f'Mark {habit.name} done for {period}?', default=True)


def _confirm_focused_stats(habit: Habit) -> bool:
    render.before_prompts()
    return Confirm.ask(f'View focused Stats for {habit.name}?', default=True)


def _choose_ending() -> str | None:
    render.before_prompts()
    return questionary.select(
        'Where would you like to go next?',
        choices=[
            questionary.Choice(title='Enter interactive home', value='home'),
            questionary.Choice(title='Exit', value='exit'),
        ],
        style=render.select_style,
    ).ask()


def _quoted(value: str) -> str:
    return f'"{value.replace(chr(34), chr(92) + chr(34))}"'


def _show_command(command: str) -> None:
    with render.view():
        render.note('Equivalent explicit command:')
        render.note(f'[cyan]{escape(command)}[/cyan]')


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
        render.heading('Quick start', symbol=_QUICK_START_ICON)
        render.note('A Habit repeats once in each Daily or Weekly Period.')
        render.note(
            'Daily means once per calendar day. Weekly means once per ISO week.'
        )

    name = _ask_display_name(profile.username)
    if name:
        profile = profile_service.update_display_name(name)

    existing = habit_service.list_habits(active_only=False)
    relevant_habit: Habit | None = None
    sample_data = False
    if not existing:
        choice = _choose_beginning()
        if choice is None:
            raise Exit()
        if choice == 'sample':
            seed()
            sample_data = True
        elif choice == 'personal':
            previous_ids = {habit.id for habit in existing}
            add()
            created = [
                habit
                for habit in habit_service.list_habits(active_only=True)
                if habit.id not in previous_ids
            ]
            if created:
                relevant_habit = created[0]
                repetition = relevant_habit.periodicity.value.lower()
                icon_option = ' --icon' if relevant_habit.icon else ''
                _show_command(
                    f'habit add {_quoted(relevant_habit.name)} '
                    f'--every {repetition}{icon_option}'
                )
    else:
        with render.view():
            render.note('Your habits and history stay unchanged during this tour.')

    habits = habit_service.list_habits(active_only=False)
    if sample_data:
        with render.view():
            render.note(
                'This generated history is Sample data, not your personal progress.'
            )
    if relevant_habit is None:
        active = [habit for habit in habits if habit.is_active]
        due_ids = {habit.id for habit in habit_service.get_due_habits()}
        relevant_habit = next(
            (habit for habit in active if habit.id in due_ids),
            active[0] if active else (habits[0] if habits else None),
        )

    if habits:
        today()
        _show_command('habit today')
    if relevant_habit is not None and not sample_data:
        relevant_habit = _offer_first_completion(habit_service, relevant_habit)
    if relevant_habit is not None:
        _offer_focused_stats(relevant_habit)

    _finish(profile.username)


def _offer_first_completion(habit_service: HabitService, habit: Habit) -> Habit:
    if not habit.is_active:
        return habit
    due_habits = habit_service.get_due_habits()
    due_ids = {item.id for item in due_habits}
    if habit.id not in due_ids:
        with render.view():
            render.note(
                'Nothing is Due, so there is no Completion to record in this tour.'
            )
        return habit
    if not _confirm_first_completion(habit):
        return habit
    try:
        done()
    except Exit as error:
        if error.exit_code not in (0, None):
            raise
        return habit
    remaining_due_ids = {item.id for item in habit_service.get_due_habits()}
    completed_habit = next(
        item for item in due_habits if item.id not in remaining_due_ids
    )
    _show_command(f'habit done {_quoted(completed_habit.name)}')
    with render.view():
        render.note(
            'The +1 XP and Current streak above came from this routine Completion.'
        )
        render.note(
            'Milestones at 3, 7, 14, and 30 consecutive Periods award '
            'five bonus XP once per Habit.'
        )
    return completed_habit


def _offer_focused_stats(habit: Habit) -> None:
    if not _confirm_focused_stats(habit):
        return
    stats(habit.name, archived=not habit.is_active)
    archived = ' --archived' if not habit.is_active else ''
    _show_command(f'habit stats {_quoted(habit.name)}{archived}')


def _finish(display_name: str) -> None:
    with render.view():
        render.success(f"You're ready, {display_name}.")
        render.note('Run [cyan]habit[/cyan] whenever you want to check in.')
        render.note('Full user guide:')
        render.note(USER_GUIDE_URL)
    if _choose_ending() == 'home':
        home()
