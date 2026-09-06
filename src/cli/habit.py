import sys
from datetime import datetime
from typing import Annotated

import questionary
from rich.prompt import Confirm, Prompt
from typer import Argument, Exit, Option

from src.cli import render
from src.core.analytics import CompletionDTO, CurrentStreakDTO, HabitDTO
from src.core.analytics import current_streak_for_habit as calculate_current_streak
from src.core.db import get_session
from src.core.habit import (
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitArchivedNameExists,
    HabitNotFound,
    HabitService,
)
from src.core.models import Completion, Habit, Periodicity, require_persisted_id
from src.core.xp import XPService

_REPETITION_ALIASES = {
    'day': Periodicity.DAILY,
    'daily': Periodicity.DAILY,
    'week': Periodicity.WEEKLY,
    'weekly': Periodicity.WEEKLY,
}
_CUSTOM_ICON = '__custom__'
_NO_ICON = '__none__'
_KEEP_ICON = '__keep__'
_CLEAR_ICON = '__clear__'
_SUGGESTED_ICONS = (
    ('📚', 'Reading'),
    ('💧', 'Water'),
    ('🏃', 'Movement'),
    ('🧘', 'Mindfulness'),
    ('📝', 'Writing'),
    ('🥗', 'Food'),
    ('😴', 'Sleep'),
    ('💪', 'Strength'),
    ('🧹', 'Chores'),
    ('🎯', 'Focus'),
)


def _can_prompt() -> bool:
    return sys.stdin.isatty()


def _repetition_label(periodicity: Periodicity) -> str:
    return 'Daily' if periodicity == Periodicity.DAILY else 'Weekly'


def _parse_repetition(value: str) -> Periodicity | None:
    return _REPETITION_ALIASES.get(value.strip().casefold())


def _habit_service() -> HabitService:
    return HabitService(get_session)


def _completing_habit_service() -> tuple[HabitService, XPService]:
    xp_service = XPService(get_session)
    return HabitService(get_session, xp_service=xp_service), xp_service


def _current_period_phrase(periodicity: Periodicity) -> str:
    return 'today' if periodicity == Periodicity.DAILY else 'this week'


def _streak_label(streak: int, periodicity: Periodicity) -> str:
    unit = 'day' if periodicity == Periodicity.DAILY else 'week'
    return f'{streak}-{unit} streak'


def _habit_dto(habit: Habit) -> HabitDTO:
    return HabitDTO(
        id=require_persisted_id(habit.id, 'Habit'),
        name=habit.name,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        is_active=habit.is_active,
    )


def _completion_dto(completion: Completion) -> CompletionDTO:
    return CompletionDTO(
        habit_id=completion.habit_id,
        completed_at=completion.completed_at,
        period_key=completion.period_key,
    )


def _progress_label(habit: Habit, due_ids: set[int]) -> str:
    if not habit.is_active:
        return 'Archived'
    habit_id = require_persisted_id(habit.id, 'Habit')
    return 'Due' if habit_id in due_ids else 'Done'


def _current_streak_cell(habit: Habit, streak: CurrentStreakDTO) -> str:
    if not habit.is_active:
        return '—'
    if streak.length > 0:
        symbol = '⏳' if streak.pending else '🔥'
        return f'{symbol} {streak.length}'
    if streak.has_history:
        return '❄ Broken'
    return '—'


def _picker_label(habit: Habit) -> str:
    prefix = _icon_prefix(habit.icon)
    return f'{prefix}{habit.name} ({_current_period_phrase(habit.periodicity)})'


def _choose_due_habit(service: HabitService) -> Habit:
    due_habits = service.get_due_habits()
    if not due_habits:
        render.warning('Nothing is due right now.')
        render.next_step('see your snapshot with [cyan]habit today[/cyan].')
        raise Exit(1)
    render.before_prompts()
    selected_id = questionary.select(
        'Which habit is done?',
        choices=[
            questionary.Choice(title=_picker_label(habit), value=habit.id)
            for habit in due_habits
        ],
        style=render.select_style,
    ).ask()
    if selected_id is None:
        raise Exit()
    return next(habit for habit in due_habits if habit.id == selected_id)


def _prompt_icon(
    *,
    habit_name: str | None = None,
    current: str | None = None,
    allow_keep: bool = False,
    allow_clear: bool = False,
) -> str | None:
    choices = []
    if allow_keep:
        current_label = (
            f'{_icon_prefix(current)}{habit_name or "current Icon"}'.rstrip()
        )
        choices.append(
            questionary.Choice(
                title=f'Keep current Icon ({current_label})',
                value=_KEEP_ICON,
            )
        )
    choices.extend(
        questionary.Choice(title=f'{icon}  {label}', value=icon)
        for icon, label in _SUGGESTED_ICONS
    )
    choices.append(questionary.Choice(title='Custom symbol', value=_CUSTOM_ICON))
    if allow_clear:
        choices.append(questionary.Choice(title='Clear Icon', value=_CLEAR_ICON))
    else:
        choices.append(questionary.Choice(title='No Icon', value=_NO_ICON))

    prompt = f'Choose an Icon for {habit_name}:' if habit_name else 'Choose an Icon:'
    render.before_prompts()
    selected = questionary.select(
        prompt,
        choices=choices,
        style=render.select_style,
    ).ask()
    if selected is None:
        raise Exit()
    if selected in {_NO_ICON, _CLEAR_ICON}:
        return None
    if selected == _KEEP_ICON:
        return _KEEP_ICON
    if selected != _CUSTOM_ICON:
        return selected

    render.before_prompts()
    custom = Prompt.ask('Custom symbol').strip()
    if not custom:
        if allow_keep:
            raise Exit()
        return None
    return custom


def _ask_for_another_name() -> str:
    if not _can_prompt():
        raise Exit(1)
    render.before_prompts()
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
    pick_icon: Annotated[
        bool,
        Option('--icon', '-i', help='Choose an Icon interactively'),
    ] = False,
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
        render.before_prompts()
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
        render.before_prompts()
        every_choice = questionary.select(
            'How often?',
            choices=[
                questionary.Choice(title='Daily', value='daily'),
                questionary.Choice(title='Weekly', value='weekly'),
            ],
            style=render.select_style,
        ).ask()
        if not every_choice:
            raise Exit()
        every = every_choice
        interactive_creation = True

    if pick_icon and not _can_prompt():
        _require_icon_picker(
            next_step=(
                'run this command in a terminal, or omit --icon to store no Icon.'
            )
        )

    icon: str | None = None
    if pick_icon or interactive_creation:
        icon = _prompt_icon(habit_name=name)

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
            render.next_step(
                'restore it with [cyan]habit restore[/cyan], or choose another name.'
            )
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

        now = datetime.now()
        due_ids = {
            require_persisted_id(habit.id, 'Habit')
            for habit in service.get_due_habits(when=now)
        }
        completion_dtos = [
            _completion_dto(completion)
            for completion in service.list_completions(
                habit_ids=[require_persisted_id(habit.id, 'Habit') for habit in habits]
            )
        ]

        render.heading('Habits')
        rows = []
        row_styles: list[str | None] = []
        for habit in habits:
            streak = calculate_current_streak(
                _habit_dto(habit), completion_dtos, now=now
            )
            rows.append(
                [
                    str(require_persisted_id(habit.id, 'Habit')),
                    render.labelled_habit(habit.name, habit.icon),
                    _progress_label(habit, due_ids),
                    _current_streak_cell(habit, streak),
                    _repetition_label(habit.periodicity),
                ]
            )
            row_styles.append('yellow' if not habit.is_active else None)
        render.table(
            ['ID', 'Habit', 'Progress', 'Streak', 'Repetition'],
            rows,
            row_styles=row_styles,
        )
        if archived:
            render.blank()
            render.warning('Includes archived habits.')


def done(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
) -> None:
    """Mark a habit done for the current period."""
    service, xp_service = _completing_habit_service()

    if selector is None or not selector.strip():
        if not _can_prompt():
            render.error('Choose a habit to mark done.')
            render.next_step('mark one with [cyan]habit done NAME_OR_ID[/cyan].')
            raise Exit(1)
        habit = _choose_due_habit(service)
    else:
        try:
            habit = service.get_habit(selector)
        except HabitNotFound:
            render.error(f"No habit matches '{selector}'.")
            render.next_step('list habits with [cyan]habit list[/cyan].')
            raise Exit(1)

    habit_id = require_persisted_id(habit.id, 'Habit')
    level_before, _, _ = xp_service.get_level_progress_for_active_profile()
    try:
        completion, milestone_events = service.complete_habit(habit_id)
    except HabitArchived:
        render.error(f"'{habit.name}' is archived and cannot be marked done.")
        raise Exit(1)
    except HabitAlreadyCompletedForPeriod:
        render.error(
            f"'{habit.name}' is already done for {_current_period_phrase(habit.periodicity)}."
        )
        raise Exit(1)

    label = render.labelled_habit(habit.name, habit.icon)
    period = _current_period_phrase(habit.periodicity)
    current = calculate_current_streak(
        _habit_dto(habit),
        [
            _completion_dto(item)
            for item in service.list_completions(habit_ids=[habit_id])
        ],
        now=completion.completed_at,
    )
    level_after, _, _ = xp_service.get_level_progress_for_active_profile()
    due_habits = service.get_due_habits()
    with render.view():
        render.success(f'{label} is done for {period}.')
        render.note(f'+1 XP · {_streak_label(current.length, habit.periodicity)}')
        if milestone_events:
            bonus = sum(event.amount for event in milestone_events)
            render.success(
                f'Milestone: {_streak_label(current.length, habit.periodicity)}. +{bonus} XP'
            )
        if level_after > level_before:
            render.success(f'Level up: Level {level_after}.')
        if due_habits:
            remaining = len(due_habits)
            waiting = 'habit is' if remaining == 1 else 'habits are'
            render.next_step(
                f'{remaining} {waiting} still waiting. Run [cyan]habit today[/cyan].'
            )
        else:
            render.next_step('see your snapshot with [cyan]habit today[/cyan].')


def _icon_prefix(icon: str | None) -> str:
    visible = render.visible_icon(icon)
    return f'{visible} ' if visible else ''


def _choice_label(habit: Habit) -> str:
    prefix = _icon_prefix(habit.icon)
    status = '' if habit.is_active else ' — archived'
    return f'{prefix}{habit.name} ({_repetition_label(habit.periodicity)}){status}'


def _choose_habit(habits: list[Habit], prompt: str) -> Habit:
    render.before_prompts()
    selected_id = questionary.select(
        prompt,
        choices=[
            questionary.Choice(title=_choice_label(habit), value=habit.id)
            for habit in habits
        ],
        style=render.select_style,
    ).ask()
    if selected_id is None:
        raise Exit()
    return next(habit for habit in habits if habit.id == selected_id)


def _resolve_habit(
    service: HabitService,
    selector: str | None,
    *,
    prompt: str,
    picker_habits: list[Habit],
    missing_example: str,
    empty_message: str,
    not_found_next_step: str = 'list habits with [cyan]habit list[/cyan].',
) -> Habit:
    if selector is None or not selector.strip():
        if not _can_prompt():
            render.error('Choose a habit.')
            render.next_step(missing_example)
            raise Exit(1)
        if not picker_habits:
            render.warning(empty_message)
            raise Exit(1)
        return _choose_habit(picker_habits, prompt)
    try:
        return service.get_habit(selector)
    except HabitNotFound:
        render.error(f"No habit matches '{selector}'.")
        render.next_step(not_found_next_step)
        raise Exit(1)


def _apply_habit_update(
    service: HabitService,
    habit: Habit,
    *,
    name: str | None,
    icon: str | None,
    clear_icon: bool,
    include_archived: bool,
) -> Habit:
    habit_id = require_persisted_id(habit.id, 'Habit')
    try:
        return service.update_habit(
            habit_id,
            name=name,
            icon=icon,
            clear_icon=clear_icon,
            include_archived=include_archived,
        )
    except HabitArchived:
        render.error(f"'{habit.name}' is archived.")
        render.next_step('edit it with [cyan]habit edit NAME --archived[/cyan].')
        raise Exit(1)
    except HabitAlreadyExists as error:
        render.error(f"A habit named '{error.name}' already exists.")
        raise Exit(1)
    except HabitArchivedNameExists as error:
        render.error(str(error))
        raise Exit(1)
    except ValueError as error:
        render.error(str(error))
        raise Exit(1)


def _choose_edit_action() -> str | None:
    render.before_prompts()
    return questionary.select(
        'What would you like to change?',
        choices=[
            questionary.Choice(title='Change name', value='name'),
            questionary.Choice(title='Change Icon', value='icon'),
            questionary.Choice(title='Clear Icon', value='clear'),
            questionary.Choice(title='Back', value='back'),
        ],
        style=render.select_style,
    ).ask()


def _require_icon_picker(*, next_step: str) -> None:
    if _can_prompt():
        return
    render.error('The Icon picker needs an interactive terminal.')
    render.next_step(next_step)
    raise Exit(1)


def _show_habit_updated(habit: Habit) -> None:
    label = render.labelled_habit(habit.name, habit.icon)
    with render.view():
        render.success(f'{label} was updated.')
        render.next_step('see it with [cyan]habit list[/cyan].')


def edit(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
    name: Annotated[
        str | None, Option('--name', '-n', help='New displayed name')
    ] = None,
    pick_icon: Annotated[
        bool,
        Option('--icon', '-i', help='Choose an Icon interactively'),
    ] = False,
    clear_icon: Annotated[
        bool, Option('--clear-icon', help='Remove the current Icon')
    ] = False,
    archived: Annotated[
        bool,
        Option('--archived', '-a', help='Allow editing an archived habit'),
    ] = False,
) -> None:
    """Edit a habit's name or icon."""
    if pick_icon and clear_icon:
        render.error('Choose either --icon or --clear-icon, not both.')
        raise Exit(1)

    service = _habit_service()
    picker_habits = service.list_habits(active_only=not archived)
    habit = _resolve_habit(
        service,
        selector,
        prompt='Which habit should be edited?',
        picker_habits=picker_habits,
        missing_example=(
            'edit one with [cyan]habit edit NAME --name "New name"[/cyan].'
        ),
        empty_message=(
            'No archived habits found.' if archived else 'No active habits found.'
        ),
    )
    if not habit.is_active and not archived:
        render.error(f"'{habit.name}' is archived.")
        render.next_step('edit it with [cyan]habit edit NAME --archived[/cyan].')
        raise Exit(1)

    picker_next_step = (
        'run this command in a terminal, or use '
        '[cyan]habit edit NAME --clear-icon[/cyan].'
    )
    if pick_icon:
        _require_icon_picker(next_step=picker_next_step)

    if name is None and not pick_icon and not clear_icon:
        if not _can_prompt():
            render.error('Choose a name or Icon to change.')
            render.next_step(
                'edit with [cyan]habit edit NAME --name "New name"[/cyan].'
            )
            raise Exit(1)
        action = _choose_edit_action()
        if action is None or action == 'back':
            raise Exit()
        if action == 'name':
            render.before_prompts()
            name = Prompt.ask('New name', default=habit.name).strip()
            if not name:
                render.error('Habit name cannot be empty.')
                raise Exit(1)
        elif action == 'icon':
            pick_icon = True
        elif action == 'clear':
            clear_icon = True

    icon: str | None = None
    kept_icon = False
    if pick_icon:
        _require_icon_picker(next_step=picker_next_step)
        chosen = _prompt_icon(
            habit_name=habit.name,
            current=habit.icon,
            allow_keep=True,
            allow_clear=True,
        )
        if chosen == _KEEP_ICON:
            kept_icon = True
        elif chosen is None:
            clear_icon = True
        else:
            icon = chosen

    if name is None and icon is None and not clear_icon:
        if kept_icon:
            _show_habit_updated(habit)
            return
        raise Exit()

    updated = _apply_habit_update(
        service,
        habit,
        name=name,
        icon=icon,
        clear_icon=clear_icon,
        include_archived=archived,
    )
    _show_habit_updated(updated)


def archive_habit(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
    force: Annotated[bool, Option('--force', '-f', help='Skip confirmation')] = False,
) -> None:
    """Archive a habit while keeping its history."""
    service = _habit_service()
    habit = _resolve_habit(
        service,
        selector,
        prompt='Which habit should be archived?',
        picker_habits=service.list_habits(active_only=True),
        missing_example='archive one with [cyan]habit archive NAME_OR_ID[/cyan].',
        empty_message='No active habits found.',
    )
    if not habit.is_active:
        render.error(f"'{habit.name}' is already archived.")
        render.next_step('restore it with [cyan]habit restore[/cyan].')
        raise Exit(1)

    if not force:
        render.before_prompts()
        if not Confirm.ask(f"Archive '{habit.name}' and keep its history?"):
            render.warning('Cancelled.')
            raise Exit()

    archived = service.archive_habit(require_persisted_id(habit.id, 'Habit'))
    label = render.labelled_habit(archived.name, archived.icon)
    with render.view():
        render.success(f'{label} was archived.')
        render.note('Completions and XP are kept.')
        render.next_step('restore it later with [cyan]habit restore[/cyan].')


def restore(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
) -> None:
    """Restore an archived habit to active tracking."""
    service = _habit_service()
    archived_habits = [
        habit for habit in service.list_habits(active_only=False) if not habit.is_active
    ]
    habit = _resolve_habit(
        service,
        selector,
        prompt='Which habit should be restored?',
        picker_habits=archived_habits,
        missing_example='restore one with [cyan]habit restore NAME_OR_ID[/cyan].',
        empty_message='No archived habits found.',
        not_found_next_step=(
            'list archived habits with [cyan]habit list --archived[/cyan].'
        ),
    )
    if habit.is_active:
        render.error(f"'{habit.name}' is already active.")
        raise Exit(1)

    try:
        restored = service.restore_habit(require_persisted_id(habit.id, 'Habit'))
    except HabitAlreadyExists as error:
        render.error(f"A habit named '{error.name}' already exists.")
        raise Exit(1)
    except HabitArchivedNameExists as error:
        render.error(str(error))
        raise Exit(1)

    label = render.labelled_habit(restored.name, restored.icon)
    with render.view():
        render.success(f'{label} is active again.')
        render.next_step('see it with [cyan]habit list[/cyan].')


def delete_habit(
    selector: Annotated[str | None, Argument(help='Habit ID or name')] = None,
    force: Annotated[bool, Option('--force', '-f', help='Skip confirmation')] = False,
) -> None:
    """Permanently delete a habit and its history."""
    service = _habit_service()
    habit = _resolve_habit(
        service,
        selector,
        prompt='Which habit should be permanently deleted?',
        picker_habits=service.list_habits(active_only=False),
        missing_example='delete one with [cyan]habit delete NAME_OR_ID[/cyan].',
        empty_message='No habits found.',
    )
    habit_id = require_persisted_id(habit.id, 'Habit')
    impact = service.preview_delete(habit_id)
    if not force:
        warning = (
            f'Permanently delete "{habit.name}"? This removes '
            f'{impact.completion_count} completions and {impact.xp_amount} XP. '
            'Historical stats will change. This cannot be undone. Continue?'
        )
        render.before_prompts()
        if not Confirm.ask(warning, default=False):
            render.warning('Cancelled.')
            raise Exit()

    deleted = service.delete_habit(habit_id)
    label = render.labelled_habit(habit.name, habit.icon)
    with render.view():
        render.success(f'{label} was permanently deleted.')
        render.note(
            f'Removed {deleted.completion_count} completions and {deleted.xp_amount} XP.'
        )
        render.next_step('see remaining habits with [cyan]habit list[/cyan].')
