"""Home and daily snapshot commands."""

import sys
from collections.abc import Iterator
from datetime import datetime
from typing import Annotated

import questionary
from rich.live import Live
from rich.panel import Panel
from sqlmodel import Session
from typer import Exit, Option

from src.cli import render
from src.cli.analytics import stats
from src.cli.habit import add, done, show_habits
from src.cli.keys import drain_pending_keys, read_key
from src.cli.settings import edit_settings
from src.core.db import session_scope
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


def _supports_live() -> bool:
    return sys.stdin.isatty() and render.console.is_terminal


def _choose_action() -> str | None:
    return questionary.select(
        'What would you like to do?',
        choices=[
            questionary.Choice(title=label, value=value)
            for value, label, _handler in _HOME_ACTIONS
        ],
    ).unsafe_ask()


def _live_choose() -> str | None:
    cursor = 0
    with Live(
        _home_panel(cursor=cursor),
        console=render.console,
        auto_refresh=False,
        transient=True,
    ) as live:
        while True:
            key = read_key()
            if key == 'up':
                cursor = (cursor - 1) % len(_HOME_ACTIONS)
            elif key == 'down':
                cursor = (cursor + 1) % len(_HOME_ACTIONS)
            elif key == 'enter':
                return _HOME_ACTIONS[cursor][0]
            elif key == 'esc':
                return None
            else:
                continue
            live.update(_home_panel(cursor=cursor), refresh=True)


def _greeting(display_name: str) -> str:
    hour = datetime.now().hour
    if hour < 12:
        period = 'morning'
    elif hour < 17:
        period = 'afternoon'
    else:
        period = 'evening'
    return f'Good {period}, {display_name}'


def _emit_snapshot(*, include_done: bool = False) -> None:
    with session_scope() as session:

        def factory() -> Iterator[Session]:
            return iter((session,))

        profile_service = ProfileService(factory)
        habit_service = HabitService(factory)
        xp_service = XPService(factory)

        profile = profile_service.ensure_single_profile()
        active_habits = habit_service.list_habits(active_only=True)

        render.heading(_greeting(profile.username))
        render.blank()

        if not active_habits:
            render.warning('No habits yet.')
            render.next_step('add one with [cyan]habit add[/cyan].')
            return

        due_habits = habit_service.get_due_habits()
        due_ids = {habit.id for habit in due_habits}
        completed_habits = (
            [habit for habit in active_habits if habit.id not in due_ids]
            if include_done
            else []
        )
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
        done_today = [
            habit
            for habit in completed_habits
            if habit.periodicity == Periodicity.DAILY
        ]
        due_this_week = [
            habit for habit in due_habits if habit.periodicity == Periodicity.WEEKLY
        ]
        done_this_week = [
            habit
            for habit in completed_habits
            if habit.periodicity == Periodicity.WEEKLY
        ]
        daily_title = 'Today' if include_done else 'Due today'
        weekly_title = 'This week' if include_done else 'Due this week'

        render.list_section(
            daily_title,
            [render.labelled_habit(habit.name, habit.icon) for habit in due_today],
            done_names=[
                render.labelled_habit(habit.name, habit.icon) for habit in done_today
            ],
        )
        render.list_section(
            weekly_title,
            [render.labelled_habit(habit.name, habit.icon) for habit in due_this_week],
            done_names=[
                render.labelled_habit(habit.name, habit.icon)
                for habit in done_this_week
            ],
        )

        if not due_habits:
            render.blank()
            render.success('All habits are done for now.')


def _home_panel(*, cursor: int = 0) -> Panel:
    with render.collecting() as parts:
        _emit_snapshot()
        render.menu(
            'What would you like to do?',
            [label for _value, label, _handler in _HOME_ACTIONS],
            cursor=cursor,
        )
    render.discard_notice()
    return render.panel(parts)


def today(
    include_done: Annotated[
        bool,
        Option('--done', help='Include completed active habits'),
    ] = False,
) -> None:
    """Show a snapshot of habits due today and this week."""
    with render.view():
        _emit_snapshot(include_done=include_done)


def home() -> None:
    """Open interactive home, or print the read-only today snapshot."""
    if not _can_prompt():
        today()
        return
    try:
        _run_home()
    except KeyboardInterrupt:
        raise Exit() from None


def _after_action() -> AfterAction:
    with session_scope() as session:
        profile = ProfileService(lambda: iter((session,))).ensure_single_profile()
        return profile.after_action


def _clear_home() -> None:
    if render.console.is_terminal:
        render.console.clear()


def _wait_to_return_home() -> bool:
    """True redraws home. False leaves interactive mode."""
    render.note('Press Enter to return home. Esc to exit.')
    if not sys.stdin.isatty():
        return True
    drain_pending_keys()
    while True:
        key = read_key()
        if key == 'enter':
            return True
        if key == 'esc':
            return False


def _pause_and_clear() -> bool:
    """Wait to return home. True means redraw. False means leave."""
    if not _wait_to_return_home():
        return False
    _clear_home()
    return True


def _run_home() -> None:
    handlers = {
        value: handler
        for value, _label, handler in _HOME_ACTIONS
        if handler is not None
    }
    while True:
        if _supports_live():
            choice = _live_choose()
        else:
            render.console.print()
            render.console.print(_home_panel())
            render.console.print()
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
            render.discard_notice()
            if error.exit_code in (0, None):
                _clear_home()
                continue
            if _after_action() == AfterAction.EXIT:
                raise
            if not _pause_and_clear():
                return
            continue
        render.discard_notice()
        if _after_action() == AfterAction.EXIT:
            return
        if not _pause_and_clear():
            return
