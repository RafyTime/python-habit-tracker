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
    filter_habits_by_periodicity,
    longest_streak_across_habits,
    longest_streak_for_habit,
)
from src.core.db import get_session
from src.core.habit import ActiveProfileRequired, HabitService
from src.core.models import Periodicity

cli = Typer()
console = Console()


class AnalyticsCLIContext:
    """Context object for analytics CLI commands."""

    def __init__(self) -> None:
        self.habit_service = HabitService(get_session)


@cli.callback()
def analytics_callback(ctx: Context) -> None:
    """Initialize habit service in context."""
    ctx.obj = AnalyticsCLIContext()


def _habit_to_dto(habit) -> HabitDTO:
    """Convert Habit ORM model to HabitDTO."""
    return HabitDTO(
        id=habit.id,
        name=habit.name,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        is_active=habit.is_active,
    )


def _completion_to_dto(completion) -> CompletionDTO:
    """Convert Completion ORM model to CompletionDTO."""
    return CompletionDTO(
        habit_id=completion.habit_id,
        completed_at=completion.completed_at,
        period_key=completion.period_key,
    )


@cli.command()
def habits(
    ctx: Context,
    periodicity: Annotated[
        str | None,
        Option('--periodicity', '-p', help='Filter by periodicity: daily or weekly'),
    ] = None,
):
    """List all habits with analytics information."""
    service: HabitService = ctx.obj.habit_service

    try:
        periodicity_enum: Periodicity | None = None
        if periodicity:
            periodicity_upper = periodicity.upper()
            if periodicity_upper not in ['DAILY', 'WEEKLY']:
                print(
                    f"[red]Invalid periodicity '{periodicity}'. Must be 'daily' or 'weekly'.[/red]"
                )
                raise Exit(code=1)
            periodicity_enum = Periodicity(periodicity_upper)

        # Fetch all habits
        habits_orm = service.list_habits(active_only=False)
        habits_dto = [_habit_to_dto(h) for h in habits_orm]

        if not habits_dto:
            print('[yellow]No habits found. Create one with "habit create".[/yellow]')
            return

        # Apply periodicity filter if provided
        if periodicity_enum:
            habits_dto = filter_habits_by_periodicity(habits_dto, periodicity_enum)

        # Render table
        table = Table(title='Habits')
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

    except ActiveProfileRequired:
        print('[yellow]No active profile set. Use "profile switch" to set one.[/yellow]')
        print('[dim]Tip: Create a profile with "profile create" if you don\'t have one.[/dim]')


@cli.command()
def longest(
    ctx: Context,
    habit: Annotated[
        str | None,
        Option('--habit', '-H', help='Habit ID or name to check streak for'),
    ] = None,
):
    """Show the longest streak across habits or for a specific habit."""
    service: HabitService = ctx.obj.habit_service

    try:
        # Fetch all habits
        habits_orm = service.list_habits(active_only=False)
        habits_dto = [_habit_to_dto(h) for h in habits_orm]

        if not habits_dto:
            if habit:
                print(f"[red]Habit '{habit}' not found.[/red]")
                raise Exit(code=1)
            else:
                print('[yellow]No habits found. Create one with "habit create".[/yellow]')
                return

        # Fetch completions
        habit_ids = [h.id for h in habits_orm]
        completions_orm = service.list_completions(habit_ids=habit_ids)
        completions_dto = [_completion_to_dto(c) for c in completions_orm]

        # Handle specific habit request
        if habit:
            # Try to resolve habit by ID or name
            target_habit_dto = None
            try:
                habit_id = int(habit)
                target_habit_dto = next((h for h in habits_dto if h.id == habit_id), None)
            except ValueError:
                # Not a number, try name match (case-insensitive)
                habit_name_lower = habit.lower()
                target_habit_dto = next(
                    (h for h in habits_dto if h.name.lower() == habit_name_lower), None
                )

            if not target_habit_dto:
                print(f"[red]Habit '{habit}' not found.[/red]")
                raise Exit(code=1)

            streak = longest_streak_for_habit(target_habit_dto, completions_dto)

            # Show result
            if completions_dto:
                periodicity_label = (
                    'days' if target_habit_dto.periodicity == Periodicity.DAILY else 'weeks'
                )
                print(
                    Panel.fit(
                        f"[bold]Longest Streak:[/bold] {streak} {periodicity_label}\n"
                        f"[bold]Habit:[/bold] {target_habit_dto.name}\n"
                        f"[bold]Periodicity:[/bold] {target_habit_dto.periodicity.value}",
                        title='Streak Information',
                        border_style='green',
                    )
                )
            else:
                print(
                    Panel.fit(
                        f"[bold]Longest Streak:[/bold] 0\n"
                        f"[bold]Habit:[/bold] {target_habit_dto.name}\n"
                        f"[dim]No completions recorded yet. Complete this habit to start building your streak![/dim]",
                        title='Streak Information',
                        border_style='yellow',
                    )
                )
            return

        # Show longest streak across all habits
        result = longest_streak_across_habits(habits_dto, completions_dto)

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
            periodicity_label = 'days' if result.periodicity == Periodicity.DAILY else 'weeks'
            print(
                Panel.fit(
                    f"[bold]Longest Streak:[/bold] {result.length} {periodicity_label}\n"
                    f"[bold]Habit:[/bold] {result.habit_name}\n"
                    f"[bold]Periodicity:[/bold] {result.periodicity.value if result.periodicity else 'N/A'}",
                    title='Longest Streak',
                    border_style='green',
                )
            )

    except ActiveProfileRequired:
        print('[yellow]No active profile set. Use "profile switch" to set one.[/yellow]')
        print('[dim]Tip: Create a profile with "profile create" if you don\'t have one.[/dim]')
