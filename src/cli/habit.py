from typing import Annotated

import questionary
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Context, Exit, Option, Typer

from src.core.db import get_session
from src.core.habit import (
    ActiveProfileRequired,
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitNotFound,
    HabitService,
)
from src.core.models import Periodicity
from src.core.xp import XPService

cli = Typer()
console = Console()


class HabitCLIContext:
    """Context object for habit CLI commands."""

    def __init__(self) -> None:
        self.xp_service = XPService(get_session)
        self.habit_service = HabitService(get_session, xp_service=self.xp_service)


@cli.callback()
def habit_callback(ctx: Context) -> None:
    """Initialize habit service in context."""
    ctx.obj = HabitCLIContext()


@cli.command()
def create(
    ctx: Context,
    name: Annotated[str | None, Argument(help='The name of the habit')] = None,
    periodicity: Annotated[
        str | None,
        Option('--periodicity', '-p', help='Periodicity: daily or weekly'),
    ] = None,
):
    """Create a new habit."""
    service: HabitService = ctx.obj.habit_service

    print(Panel.fit('Create a New Habit', style='bold blue'))

    try:
        # Get name
        if not name:
            name = Prompt.ask('Enter habit name').strip()

        if not name:
            print('[red]Habit name cannot be empty.[/red]')
            raise Exit(1)

        # Get periodicity
        if not periodicity:
            periodicity_choice = questionary.select(
                'Select periodicity:',
                choices=[
                    questionary.Choice(title='Daily', value='daily'),
                    questionary.Choice(title='Weekly', value='weekly'),
                ],
            ).ask()

            if not periodicity_choice:
                raise Exit()

            periodicity = periodicity_choice

        # Normalize periodicity
        periodicity_upper = periodicity.upper()
        if periodicity_upper not in ['DAILY', 'WEEKLY']:
            print(f"[red]Invalid periodicity '{periodicity}'. Must be 'daily' or 'weekly'.[/red]")
            raise Exit(1)

        periodicity_enum = Periodicity(periodicity_upper)

        # Create habit
        habit = service.create_habit(name, periodicity_enum)
        print(f"[green]Habit '{habit.name}' created successfully![/green]")

        print('\n[bold]Next Steps:[/bold]')
        print(' - List habits: [cyan]habit list[/cyan]')
        print(' - Complete habit: [cyan]habit complete[/cyan]')
        print(' - View due habits: [cyan]habit due[/cyan]')

    except ActiveProfileRequired:
        print('[red]No active profile. Use "profile switch" to set an active profile.[/red]')
        raise Exit(1)
    except HabitAlreadyExists as e:
        print(f"[red]Habit '{e.name}' already exists for this profile.[/red]")
        raise Exit(1)


@cli.command('list')
def list_habits(
    ctx: Context,
    all: Annotated[
        bool, Option('--all', '-a', help='Show all habits including archived')
    ] = False,
    periodicity: Annotated[
        str | None,
        Option('--periodicity', '-p', help='Filter by periodicity: daily or weekly'),
    ] = None,
):
    """List habits for the active profile."""
    service: HabitService = ctx.obj.habit_service

    try:
        periodicity_enum = None
        if periodicity:
            periodicity_upper = periodicity.upper()
            if periodicity_upper not in ['DAILY', 'WEEKLY']:
                print(
                    f"[red]Invalid periodicity '{periodicity}'. Must be 'daily' or 'weekly'.[/red]"
                )
                raise Exit(1)
            periodicity_enum = Periodicity(periodicity_upper)

        habits = service.list_habits(active_only=not all, periodicity=periodicity_enum)

        if not habits:
            if all:
                print('[yellow]No habits found. Create one with "habit create".[/yellow]')
            else:
                print('[yellow]No active habits found. Create one with "habit create".[/yellow]')
            return

        table = Table(title='Habits')
        table.add_column('ID', justify='right', style='cyan', no_wrap=True)
        table.add_column('Name', style='magenta')
        table.add_column('Periodicity', justify='center')
        table.add_column('Status', justify='center', style='green')
        table.add_column('Created At', justify='right')

        for habit in habits:
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
def complete(
    ctx: Context,
    habit_id: Annotated[int | None, Argument(help='The ID of the habit to complete')] = None,
):
    """Mark a habit as completed for the current period."""
    service: HabitService = ctx.obj.habit_service

    try:
        if not habit_id:
            # Show due habits first, fallback to all active
            due_habits = service.get_due_habits()
            if not due_habits:
                # Fallback to all active habits
                all_habits = service.list_habits(active_only=True)
                if not all_habits:
                    print('[yellow]No habits found. Create one with "habit create".[/yellow]')
                    raise Exit(1)
                habits = all_habits
                due_habits_set = set()
            else:
                habits = due_habits
                due_habits_set = {h.id for h in due_habits}

            choices = []
            for h in habits:
                is_due = h.id in due_habits_set
                display_name = f'{h.name} ({h.periodicity.value})'
                if not is_due:
                    display_name += ' [already completed]'
                choices.append(questionary.Choice(title=display_name, value=h.id))

            habit_id = questionary.select(
                'Select habit to complete:',
                choices=choices,
            ).ask()

            if not habit_id:
                raise Exit()

        # Get habit name before completing (for display)
        all_habits = service.list_habits(active_only=False)
        habit = next((h for h in all_habits if h.id == habit_id), None)

        completion = service.complete_habit(habit_id)

        if habit:
            print(f"[green]Habit '{habit.name}' completed for this period![/green]")
        else:
            print(f"[green]Habit {habit_id} completed for this period![/green]")

        # Show XP reward
        try:
            xp_service: XPService = ctx.obj.xp_service
            total_xp = xp_service.get_total_xp_for_active_profile()
            level, xp_into_level, xp_to_next_level = xp_service.get_level_progress_for_active_profile()
            print(f"[dim]+1 XP • Level {level} ({xp_into_level}/{xp_into_level + xp_to_next_level})[/dim]")
        except ActiveProfileRequired:
            # Should not happen, but handle gracefully
            pass

    except ActiveProfileRequired:
        print('[red]No active profile. Use "profile switch" to set an active profile.[/red]')
        raise Exit(1)
    except HabitNotFound:
        print("[red]Habit not found.[/red]")
        raise Exit(1)
    except HabitArchived as e:
        print(f"[red]Habit {e.habit_id} is archived and cannot be completed.[/red]")
        raise Exit(1)
    except HabitAlreadyCompletedForPeriod as e:
        print(
            f"[yellow]Habit has already been completed for period '{e.period_key}'.[/yellow]"
        )


@cli.command()
def archive(
    ctx: Context,
    habit_id: Annotated[int | None, Argument(help='The ID of the habit to archive')] = None,
    force: Annotated[
        bool, Option('--force', '-f', help='Force archive without confirmation')
    ] = False,
):
    """Archive a habit (sets is_active=False, keeps history)."""
    service: HabitService = ctx.obj.habit_service

    try:
        if not habit_id:
            # Interactive selection
            habits = service.list_habits(active_only=True)
            if not habits:
                print('[yellow]No active habits found.[/yellow]')
                raise Exit(1)

            choices = []
            for h in habits:
                display_name = f'{h.name} ({h.periodicity.value})'
                choices.append(questionary.Choice(title=display_name, value=h.id))

            habit_id = questionary.select(
                'Select habit to archive:',
                choices=choices,
            ).ask()

            if not habit_id:
                raise Exit()

        # Get habit name for confirmation
        all_habits = service.list_habits(active_only=False)
        habit = next((h for h in all_habits if h.id == habit_id), None)
        if not habit:
            print(f"[red]Habit {habit_id} not found.[/red]")
            raise Exit(1)

        if not force:
            if not Confirm.ask(f"Are you sure you want to archive habit '{habit.name}'?"):
                print('[yellow]Operation cancelled.[/yellow]')
                return

        archived_habit = service.archive_habit(habit_id)
        print(f"[green]Habit '{archived_habit.name}' archived.[/green]")

    except ActiveProfileRequired:
        print('[red]No active profile. Use "profile switch" to set an active profile.[/red]')
        raise Exit(1)
    except HabitNotFound:
        print("[red]Habit not found.[/red]")
        raise Exit(1)


@cli.command()
def due(ctx: Context):
    """List habits that are due (not completed for the current period)."""
    service: HabitService = ctx.obj.habit_service

    try:
        due_habits = service.get_due_habits()

        if not due_habits:
            print('[green]All habits are completed for this period! Great job! 🎉[/green]')
            return

        table = Table(title='Due Habits')
        table.add_column('ID', justify='right', style='cyan', no_wrap=True)
        table.add_column('Name', style='magenta')
        table.add_column('Periodicity', justify='center')
        table.add_column('Created At', justify='right')

        for habit in due_habits:
            table.add_row(
                str(habit.id),
                habit.name,
                habit.periodicity.value,
                habit.created_at.strftime('%Y-%m-%d %H:%M'),
            )

        console.print(table)
        print('\n[dim]Complete a habit with: [cyan]habit complete[/cyan][/dim]')

    except ActiveProfileRequired:
        print('[yellow]No active profile set. Use "profile switch" to set one.[/yellow]')
        print('[dim]Tip: Create a profile with "profile create" if you don\'t have one.[/dim]')
