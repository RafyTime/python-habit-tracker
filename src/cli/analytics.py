"""Analytics CLI commands."""

from typing import Annotated

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typer import Context, Exit, Option, Typer

from src.core.analytics import (
    CompletionDTO,
    HabitDTO,
    filter_habits_by_archived_inclusion,
    filter_habits_by_periodicity,
    longest_streak_across_habits,
    longest_streak_for_habit,
)
from src.core.db import get_session
from src.core.habit import HabitService
from src.core.models import Completion, Habit, Periodicity, require_persisted_id

cli = Typer()
console = Console()
ARCHIVED_HISTORY_LABEL = 'Including archived habit history'


class AnalyticsCLIContext:
    """Context object for analytics CLI commands."""

    def __init__(self) -> None:
        self.habit_service = HabitService(get_session)


@cli.callback()
def analytics_callback(ctx: Context) -> None:
    """Initialize habit service in context."""
    ctx.obj = AnalyticsCLIContext()


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


def _print_archived_history_label(include_archived: bool) -> None:
    """Label analytics output when archived history is included."""
    if include_archived:
        print(f'[yellow]{ARCHIVED_HISTORY_LABEL}[/yellow]')


def _print_no_habits_message(
    all_habits: list[HabitDTO], include_archived: bool
) -> None:
    """Explain an empty analytics view, including the archived-history choice."""
    if all_habits and not include_archived:
        print(
            '[yellow]No active habits found. Use --include-archived to include '
            'archived habit history.[/yellow]'
        )
        return
    print('[yellow]No habits found. Create one with "habit create".[/yellow]')


def _resolve_habit(habits: list[HabitDTO], habit: str) -> HabitDTO | None:
    """Resolve a habit DTO by numeric ID or case-insensitive name."""
    try:
        habit_id = int(habit)
        return next((item for item in habits if item.id == habit_id), None)
    except ValueError:
        habit_name_lower = habit.lower()
        return next(
            (item for item in habits if item.name.lower() == habit_name_lower), None
        )


@cli.command()
def habits(
    ctx: Context,
    periodicity: Annotated[
        str | None,
        Option('--periodicity', '-p', help='Filter by periodicity: daily or weekly'),
    ] = None,
    include_archived: Annotated[
        bool,
        Option(
            '--include-archived',
            help='Include archived habits and label the historical results',
        ),
    ] = False,
):
    """List habits with analytics information."""
    service: HabitService = ctx.obj.habit_service

    periodicity_enum: Periodicity | None = None
    if periodicity:
        periodicity_upper = periodicity.upper()
        if periodicity_upper not in ['DAILY', 'WEEKLY']:
            print(
                f"[red]Invalid periodicity '{periodicity}'. Must be 'daily' or 'weekly'.[/red]"
            )
            raise Exit(code=1)
        periodicity_enum = Periodicity(periodicity_upper)

    all_habits = _all_habit_dtos(service)
    habits_dto = _habits_for_analytics(all_habits, include_archived)

    if not habits_dto:
        _print_no_habits_message(all_habits, include_archived)
        return

    # Apply periodicity filter if provided
    if periodicity_enum:
        habits_dto = filter_habits_by_periodicity(habits_dto, periodicity_enum)

    _print_archived_history_label(include_archived)
    table_title = (
        'Habits (including archived history)' if include_archived else 'Habits'
    )

    # Render table
    table = Table(title=table_title)
    table.add_column('ID', justify='right', style='cyan', no_wrap=True)
    table.add_column('Name', style='magenta')
    table.add_column('Periodicity', justify='center')
    table.add_column('Status', justify='center', style='green')
    table.add_column('Created At', justify='right')

    for habit in habits_dto:
        status = 'Active' if habit.is_active else 'Archived'
        table.add_row(
            str(habit.id),
            habit.name,
            habit.periodicity.value,
            status,
            habit.created_at.strftime('%Y-%m-%d %H:%M'),
        )

    console.print(table)


@cli.command()
def longest(
    ctx: Context,
    habit: Annotated[
        str | None,
        Option('--habit', '-H', help='Habit ID or name to check streak for'),
    ] = None,
    include_archived: Annotated[
        bool,
        Option(
            '--include-archived',
            help='Include archived habits and label the historical results',
        ),
    ] = False,
):
    """Show the longest streak across habits or for a specific habit."""
    service: HabitService = ctx.obj.habit_service

    all_habits = _all_habit_dtos(service)
    habits_dto = _habits_for_analytics(all_habits, include_archived)

    if habit:
        target_habit_dto = _resolve_habit(habits_dto, habit)
        if target_habit_dto is None:
            archived_habit = _resolve_habit(all_habits, habit)
            if archived_habit is not None and not archived_habit.is_active:
                print(
                    f"[yellow]Habit '{archived_habit.name}' is archived. "
                    'Re-run with --include-archived to include archived history.[/yellow]'
                )
                raise Exit(code=1)
            print(f"[red]Habit '{habit}' not found.[/red]")
            raise Exit(code=1)

        completions_orm = service.list_completions(habit_ids=[target_habit_dto.id])
        completions_dto = [_completion_to_dto(c) for c in completions_orm]
        streak = longest_streak_for_habit(target_habit_dto, completions_dto)
        _print_archived_history_label(include_archived)
        title = (
            'Streak Information (including archived history)'
            if include_archived
            else 'Streak Information'
        )

        if completions_dto:
            periodicity_label = (
                'days' if target_habit_dto.periodicity == Periodicity.DAILY else 'weeks'
            )
            print(
                Panel.fit(
                    f'[bold]Longest Streak:[/bold] {streak} {periodicity_label}\n'
                    f'[bold]Habit:[/bold] {target_habit_dto.name}\n'
                    f'[bold]Periodicity:[/bold] {target_habit_dto.periodicity.value}',
                    title=title,
                    border_style='green',
                )
            )
        else:
            print(
                Panel.fit(
                    f'[bold]Longest Streak:[/bold] 0\n'
                    f'[bold]Habit:[/bold] {target_habit_dto.name}\n'
                    f'[dim]No completions recorded yet. Complete this habit to start building your streak![/dim]',
                    title=title,
                    border_style='yellow',
                )
            )
        return

    if not habits_dto:
        _print_no_habits_message(all_habits, include_archived)
        return

    # Fetch completions
    habit_ids = [habit_dto.id for habit_dto in habits_dto]
    completions_orm = service.list_completions(habit_ids=habit_ids)
    completions_dto = [_completion_to_dto(c) for c in completions_orm]

    # Show longest streak across all habits
    result = longest_streak_across_habits(habits_dto, completions_dto)
    _print_archived_history_label(include_archived)

    if result.length == 0:
        if completions_dto:
            print('[yellow]No streaks found.[/yellow]')
        else:
            print(
                Panel.fit(
                    '[bold]Longest Streak:[/bold] 0\n'
                    '[dim]No completions recorded yet. Complete habits to start building streaks![/dim]',
                    title='Streak Information',
                    border_style='yellow',
                )
            )
    else:
        periodicity_label = (
            'days' if result.periodicity == Periodicity.DAILY else 'weeks'
        )
        title = (
            'Longest Streak (including archived history)'
            if include_archived
            else 'Longest Streak'
        )
        print(
            Panel.fit(
                f'[bold]Longest Streak:[/bold] {result.length} {periodicity_label}\n'
                f'[bold]Habit:[/bold] {result.habit_name}\n'
                f'[bold]Periodicity:[/bold] {result.periodicity.value if result.periodicity else "N/A"}',
                title=title,
                border_style='green',
            )
        )
