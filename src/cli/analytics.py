"""Analytics CLI commands."""

from typing import Annotated

from typer import Argument, Exit, Option

from src.cli import render
from src.core.analytics import (
    CompletionDTO,
    HabitDTO,
    filter_habits_by_archived_inclusion,
    filter_habits_by_periodicity,
    longest_streak_across_habits,
    longest_streak_for_habit,
)
from src.core.db import get_session
from src.core.habit import HabitNotFound, HabitService
from src.core.models import Completion, Habit, Periodicity, require_persisted_id


def _habit_to_dto(habit: Habit) -> HabitDTO:
    """Convert Habit ORM model to HabitDTO."""
    return HabitDTO(
        id=require_persisted_id(habit.id, 'Habit'),
        name=habit.name,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        is_active=habit.is_active,
    )


def _completion_to_dto(completion: Completion) -> CompletionDTO:
    """Convert Completion ORM model to CompletionDTO."""
    return CompletionDTO(
        habit_id=completion.habit_id,
        completed_at=completion.completed_at,
        period_key=completion.period_key,
    )


def _all_habit_dtos(service: HabitService) -> list[HabitDTO]:
    """Load all persisted habits as analytics DTOs."""
    return [_habit_to_dto(habit) for habit in service.list_habits(active_only=False)]


def _habits_for_analytics(
    all_habits: list[HabitDTO], include_archived: bool
) -> list[HabitDTO]:
    """Apply the archived-history inclusion choice."""
    return filter_habits_by_archived_inclusion(
        all_habits, include_archived=include_archived
    )


def _count_label(count: int, singular: str) -> str:
    noun = singular if count == 1 else f'{singular}s'
    return f'{count} {noun}'


def _streak_unit(periodicity: Periodicity) -> str:
    return 'day' if periodicity == Periodicity.DAILY else 'week'


def _streak_phrase(length: int, periodicity: Periodicity) -> str:
    if length == 0:
        return '0'
    unit = _streak_unit(periodicity)
    if length != 1:
        unit = f'{unit}s'
    return f'{length} {unit}'


def _overall_streak_detail(
    habits: list[HabitDTO], completions: list[Completion]
) -> str:
    result = longest_streak_across_habits(
        habits,
        [_completion_to_dto(item) for item in completions],
    )
    if result.length == 0 or result.habit_name is None or result.periodicity is None:
        return '0'
    return f'{_streak_phrase(result.length, result.periodicity)} · {result.habit_name}'


def _habit_streak_detail(habit: Habit, completions: list[Completion]) -> str:
    return _streak_phrase(
        longest_streak_for_habit(
            _habit_to_dto(habit),
            [_completion_to_dto(item) for item in completions],
        ),
        habit.periodicity,
    )


def _repetition_label(periodicity: Periodicity) -> str:
    return 'Daily' if periodicity == Periodicity.DAILY else 'Weekly'


def _label_archived_history(include_archived: bool) -> None:
    if include_archived:
        render.warning('Includes archived habit history.')


def stats(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
    archived: Annotated[
        bool,
        Option('--archived', '-a', help='Include archived habit history'),
    ] = False,
) -> None:
    """Show compact overall or per-habit progress."""
    service = HabitService(get_session)

    if selector is not None and selector.strip():
        try:
            habit = service.get_habit(selector)
        except HabitNotFound:
            render.error(f"No habit matches '{selector}'.")
            render.next_step('list habits with [cyan]habit list[/cyan].')
            raise Exit(1)
        if not habit.is_active and not archived:
            render.error(f"'{habit.name}' is archived.")
            render.next_step(
                'include it with [cyan]habit stats NAME --archived[/cyan].'
            )
            raise Exit(1)
        habit_id = require_persisted_id(habit.id, 'Habit')
        completions = service.list_completions(habit_ids=[habit_id])
        with render.view():
            render.heading(render.labelled_habit(habit.name, habit.icon))
            render.blank()
            render.stats(
                [
                    ('Repetition', _repetition_label(habit.periodicity)),
                    ('Status', 'Active' if habit.is_active else 'Archived'),
                    ('Completions', _count_label(len(completions), 'completion')),
                    ('Longest streak', _habit_streak_detail(habit, completions)),
                ]
            )
            if archived or not completions:
                render.blank()
                _label_archived_history(archived)
                if not completions:
                    render.next_step('mark a habit done with [cyan]habit done[/cyan].')
        return

    all_habits = _all_habit_dtos(service)
    habits = _habits_for_analytics(all_habits, archived)

    with render.view():
        if not habits:
            if all_habits and not archived:
                render.warning('No active habits.')
                render.next_step(
                    'include archived history with [cyan]habit stats --archived[/cyan].'
                )
                return
            render.warning('No habits yet.')
            render.next_step('add one with [cyan]habit add[/cyan].')
            return

        habit_ids = [habit.id for habit in habits]
        completions = service.list_completions(habit_ids=habit_ids)
        daily = len(filter_habits_by_periodicity(habits, Periodicity.DAILY))
        weekly = len(filter_habits_by_periodicity(habits, Periodicity.WEEKLY))
        render.heading('Stats')
        render.blank()
        render.stats(
            [
                ('Daily habits', _count_label(daily, 'habit')),
                ('Weekly habits', _count_label(weekly, 'habit')),
                ('Completions', _count_label(len(completions), 'completion')),
                ('Longest streak', _overall_streak_detail(habits, completions)),
            ]
        )
        if archived or not completions:
            render.blank()
            _label_archived_history(archived)
            if not completions:
                render.next_step('mark a habit done with [cyan]habit done[/cyan].')
