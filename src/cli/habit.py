import sys
from typing import Annotated

import questionary
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from typer import Argument, Context, Exit, Option, Typer

from src.cli import render
from src.core.db import get_session
from src.core.habit import (
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitArchivedNameExists,
    HabitNotFound,
    HabitService,
)
from src.core.models import Periodicity
from src.core.xp import XPService

_REPETITION_ALIASES = {
    'day': Periodicity.DAILY,
    'daily': Periodicity.DAILY,
    'week': Periodicity.WEEKLY,
    'weekly': Periodicity.WEEKLY,
}
_CUSTOM_ICON = '__custom__'
_NO_ICON = '__none__'
_SUGGESTED_ICONS = (
    ('📚', 'Reading'),
    ('💧', 'Water'),
    ('🏃', 'Movement'),
    ('🧘', 'Mindfulness'),
    ('📝', 'Writing'),
)

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
            print(
                f"[red]Invalid periodicity '{periodicity}'. Must be 'daily' or 'weekly'.[/red]"
            )
            raise Exit(1)

        periodicity_enum = Periodicity(periodicity_upper)

        # Create habit
        habit = service.create_habit(name, periodicity_enum)
        print(f"[green]Habit '{habit.name}' created successfully![/green]")

        print('\n[bold]Next Steps:[/bold]')
        print(' - List habits: [cyan]habit list[/cyan]')
        print(' - Complete habit: [cyan]habit complete[/cyan]')
        print(' - View due habits: [cyan]habit due[/cyan]')

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
            print(
                '[yellow]No active habits found. Create one with "habit create".[/yellow]'
            )
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


@cli.command()
def complete(
    ctx: Context,
    habit_id: Annotated[
        int | None, Argument(help='The ID of the habit to complete')
    ] = None,
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
                    print(
                        '[yellow]No habits found. Create one with "habit create".[/yellow]'
                    )
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

        _, milestone_events = service.complete_habit(habit_id)

        if habit:
            print(f"[green]Habit '{habit.name}' completed for this period![/green]")
        else:
            print(f'[green]Habit {habit_id} completed for this period![/green]')

        # Show XP reward
        xp_service: XPService = ctx.obj.xp_service
        _ = xp_service.get_total_xp_for_active_profile()
        level, xp_into_level, xp_to_next_level = (
            xp_service.get_level_progress_for_active_profile()
        )
        base_xp_line = f'[dim]+1 XP • Level {level} ({xp_into_level}/{xp_into_level + xp_to_next_level})[/dim]'
        if milestone_events:
            total_bonus = sum(e.amount for e in milestone_events)
            print(base_xp_line)
            print(f'[dim]Milestone! +{total_bonus} XP bonus[/dim]')
        else:
            print(base_xp_line)

    except HabitNotFound:
        print('[red]Habit not found.[/red]')
        raise Exit(1)
    except HabitArchived as e:
        print(f'[red]Habit {e.habit_id} is archived and cannot be completed.[/red]')
        raise Exit(1)
    except HabitAlreadyCompletedForPeriod as e:
        print(
            f"[yellow]Habit has already been completed for period '{e.period_key}'.[/yellow]"
        )


@cli.command()
def archive(
    ctx: Context,
    habit_id: Annotated[
        int | None, Argument(help='The ID of the habit to archive')
    ] = None,
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
            print(f'[red]Habit {habit_id} not found.[/red]')
            raise Exit(1)

        if not force:
            if not Confirm.ask(
                f"Are you sure you want to archive habit '{habit.name}'?"
            ):
                print('[yellow]Operation cancelled.[/yellow]')
                return

        archived_habit = service.archive_habit(habit_id)
        print(f"[green]Habit '{archived_habit.name}' archived.[/green]")
        print('[dim]Completion history and XP are retained.[/dim]')

    except HabitNotFound:
        print('[red]Habit not found.[/red]')
        raise Exit(1)


@cli.command()
def delete(
    ctx: Context,
    habit_id: Annotated[
        int | None, Argument(help='The ID of the habit to permanently delete')
    ] = None,
    force: Annotated[
        bool, Option('--force', '-f', help='Permanently delete without confirmation')
    ] = False,
):
    """Permanently delete a habit and its completion history and XP."""
    service: HabitService = ctx.obj.habit_service

    try:
        if not habit_id:
            habits = service.list_habits(active_only=False)
            if not habits:
                print('[yellow]No habits found.[/yellow]')
                raise Exit(1)

            choices = []
            for h in habits:
                status = 'archived' if not h.is_active else h.periodicity.value
                display_name = f'{h.name} ({status})'
                choices.append(questionary.Choice(title=display_name, value=h.id))

            habit_id = questionary.select(
                'Select habit to permanently delete:',
                choices=choices,
            ).ask()

            if not habit_id:
                raise Exit()

        all_habits = service.list_habits(active_only=False)
        habit = next((h for h in all_habits if h.id == habit_id), None)
        if not habit:
            print(f'[red]Habit {habit_id} not found.[/red]')
            raise Exit(1)

        if not force:
            warning = (
                f"Permanently delete habit '{habit.name}'? "
                'This removes its completion history and XP. '
                'Remaining XP totals and historical analytics will change. '
                'This cannot be undone.'
            )
            if not Confirm.ask(warning):
                print('[yellow]Operation cancelled.[/yellow]')
                return

        deleted_name = service.delete_habit(habit_id)
        print(
            f"[green]Habit '{deleted_name}' and its completion history and XP "
            'were permanently deleted.[/green]'
        )

    except HabitNotFound:
        print('[red]Habit not found.[/red]')
        raise Exit(1)


@cli.command()
def due(ctx: Context):
    """List habits that are due (not completed for the current period)."""
    service: HabitService = ctx.obj.habit_service

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


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _repetition_label(periodicity: Periodicity) -> str:
    return 'Daily' if periodicity == Periodicity.DAILY else 'Weekly'


def _parse_repetition(value: str) -> Periodicity | None:
    return _REPETITION_ALIASES.get(value.strip().casefold())


def _habit_service() -> HabitService:
    return HabitService(get_session)


def _prompt_icon() -> str | None:
    choices = [
        questionary.Choice(title=f'{icon}  {label}', value=icon)
        for icon, label in _SUGGESTED_ICONS
    ]
    choices.append(questionary.Choice(title='Enter a custom icon', value=_CUSTOM_ICON))
    choices.append(questionary.Choice(title='No icon', value=_NO_ICON))

    selected = questionary.select('Choose an icon:', choices=choices).ask()
    if selected is None:
        raise Exit()
    if selected == _NO_ICON:
        return None
    if selected != _CUSTOM_ICON:
        return selected

    custom = Prompt.ask('Icon').strip()
    if not custom:
        return None
    return custom


def _ask_for_another_name() -> str:
    if not _can_prompt():
        raise Exit(1)
    name = Prompt.ask('Choose another name').strip()
    if not name:
        render.error('Habit name cannot be empty.')
        raise Exit(1)
    return name


def add(
    name: Annotated[str | None, Argument(help='The habit name')] = None,
    every: Annotated[
        str | None,
        Option('--every', '-e', help='How often: day, daily, week, or weekly'),
    ] = None,
    icon: Annotated[
        str | None,
        Option('--icon', '-i', help='Optional short icon shown beside the name'),
    ] = None,
) -> None:
    """Add a daily or weekly habit."""
    service = _habit_service()
    interactive_creation = False

    if not name:
        if not _can_prompt():
            render.error('A habit name is required.')
            render.next_step(
                'add one with [cyan]habit add "Habit name" --every daily[/cyan].'
            )
            raise Exit(1)
        name = Prompt.ask('Habit name').strip()
        if not name:
            render.error('Habit name cannot be empty.')
            raise Exit(1)
        interactive_creation = True

    if not every:
        if not _can_prompt():
            render.error('Choose how often this habit repeats.')
            render.next_step(
                'add it with [cyan]habit add "Habit name" --every daily[/cyan].'
            )
            raise Exit(1)
        every_choice = questionary.select(
            'How often?',
            choices=[
                questionary.Choice(title='Daily', value='daily'),
                questionary.Choice(title='Weekly', value='weekly'),
            ],
        ).ask()
        if not every_choice:
            raise Exit()
        every = every_choice
        interactive_creation = True

    if icon is None and interactive_creation:
        icon = _prompt_icon()

    periodicity = _parse_repetition(every)
    if periodicity is None:
        render.error(f"Unknown repetition '{every}'. Use day, daily, week, or weekly.")
        raise Exit(1)

    while True:
        try:
            habit = service.create_habit(name, periodicity, icon=icon)
            break
        except HabitArchivedNameExists as error:
            render.error(str(error))
            name = _ask_for_another_name()
        except HabitAlreadyExists as error:
            render.error(f"A habit named '{error.name}' already exists.")
            if not _can_prompt():
                render.next_step(
                    'choose another name, or list habits with [cyan]habit list[/cyan].'
                )
                raise Exit(1)
            name = _ask_for_another_name()
        except ValueError as error:
            render.error(str(error))
            raise Exit(1)

    label = render.labelled_habit(habit.name, habit.icon)
    with render.view():
        render.success(f'{label} is set as a {_repetition_label(periodicity)} habit.')
        render.next_step('see it with [cyan]habit list[/cyan].')


def show_habits(
    archived: Annotated[
        bool,
        Option('--archived', '-a', help='Include archived habits'),
    ] = False,
    every: Annotated[
        str | None,
        Option('--every', '-e', help='Filter by day, daily, week, or weekly'),
    ] = None,
) -> None:
    """List habits."""
    service = _habit_service()

    periodicity = None
    if every:
        periodicity = _parse_repetition(every)
        if periodicity is None:
            render.error(
                f"Unknown repetition '{every}'. Use day, daily, week, or weekly."
            )
            raise Exit(1)

    habits = service.list_habits(active_only=not archived, periodicity=periodicity)

    with render.view():
        if not habits:
            if archived:
                render.warning('No habits found.')
            else:
                render.warning('No active habits yet.')
            render.next_step('add one with [cyan]habit add[/cyan].')
            return

        render.heading('Habits')
        rows = []
        row_styles: list[str | None] = []
        for habit in habits:
            rows.append(
                [
                    render.labelled_habit(habit.name, habit.icon),
                    _repetition_label(habit.periodicity),
                    'Active' if habit.is_active else 'Archived',
                ]
            )
            row_styles.append('yellow' if not habit.is_active else None)
        render.table(['Name', 'Every', 'Status'], rows, row_styles=row_styles)
        if archived:
            render.blank()
            render.warning('Includes archived habits.')
