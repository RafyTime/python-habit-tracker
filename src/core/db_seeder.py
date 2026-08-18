"""Database seeding service for evaluation fixture data."""

from collections.abc import Callable, Iterator
from datetime import datetime, timedelta

from sqlmodel import Session

from src.core.habit.errors import HabitAlreadyCompletedForPeriod, HabitAlreadyExists
from src.core.habit.service import HabitService
from src.core.models import Habit, Periodicity, require_persisted_id
from src.core.profile.service import ProfileService
from src.core.xp.service import XPService


def seed_db(
    session_factory: Callable[[], Iterator[Session]],
    reference_time: datetime | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> None:
    """
    Seed the single profile with five predefined habits and four-week histories.

    Args:
        session_factory: Callable returning a session iterator, matching get_session().
        reference_time: Instant the four-week history is anchored to. Defaults to now.
        progress_callback: Optional status updater for CLI progress output.
    """
    reference_time = reference_time or datetime.now()
    created_at = reference_time - timedelta(days=28)

    def _emit(message: str) -> None:
        if progress_callback:
            progress_callback(message)

    profile_service = ProfileService(session_factory)
    xp_service = XPService(session_factory)
    habit_service = HabitService(session_factory, xp_service=xp_service)

    _emit('Ensuring profile exists...')
    profile_service.ensure_single_profile()

    _emit('Seeding Morning Hydration (28-day streak)...')
    hydration_id = _ensure_habit(
        habit_service,
        session_factory,
        'Morning Hydration',
        Periodicity.DAILY,
        created_at,
    )
    # Inclusive daily window: reference day and the previous 27 days.
    _complete_daily_offsets(habit_service, hydration_id, reference_time, 27, 0)

    _emit('Seeding Gym Session (weekly consistency)...')
    gym_id = _ensure_habit(
        habit_service,
        session_factory,
        'Gym Session',
        Periodicity.WEEKLY,
        created_at,
    )
    _complete_weekly_mondays(habit_service, gym_id, reference_time)

    _emit('Seeding Read 10 Pages (broken streak)...')
    read_id = _ensure_habit(
        habit_service,
        session_factory,
        'Read 10 Pages',
        Periodicity.DAILY,
        created_at,
    )
    # Ten-day streak, two-day break, then sixteen days through the reference day.
    _complete_daily_offsets(habit_service, read_id, reference_time, 27, 18)
    _complete_daily_offsets(habit_service, read_id, reference_time, 15, 0)

    _emit('Seeding Code Practice (milestones 7/14)...')
    code_id = _ensure_habit(
        habit_service,
        session_factory,
        'Code Practice',
        Periodicity.DAILY,
        created_at,
    )
    # Opening week, seven-day break, then a 14-day streak that awards milestones 7 and 14.
    _complete_daily_offsets(habit_service, code_id, reference_time, 27, 21)
    _complete_daily_offsets(habit_service, code_id, reference_time, 13, 0)

    _emit('Seeding Clean Apartment (weekly edge case)...')
    clean_id = _ensure_habit(
        habit_service,
        session_factory,
        'Clean Apartment',
        Periodicity.WEEKLY,
        created_at,
    )
    _complete_weekly_calendar_edges(habit_service, clean_id, reference_time)

    _emit('Finalizing seed...')


def _ensure_habit(
    habit_service: HabitService,
    session_factory: Callable[[], Iterator[Session]],
    name: str,
    periodicity: Periodicity,
    created_at: datetime,
) -> int:
    try:
        habit = habit_service.create_habit(name, periodicity, created_at=created_at)
    except HabitAlreadyExists:
        habit = _existing_habit(habit_service, name)
    habit_id = require_persisted_id(habit.id, f'{name} habit')
    _align_created_at(session_factory, habit_id, created_at)
    return habit_id


def _align_created_at(
    session_factory: Callable[[], Iterator[Session]],
    habit_id: int,
    created_at: datetime,
) -> None:
    session = next(session_factory())
    habit = session.get(Habit, habit_id)
    if habit is None or habit.created_at == created_at:
        return
    habit.created_at = created_at
    session.add(habit)
    session.commit()


def _existing_habit(habit_service: HabitService, name: str) -> Habit:
    habit = next(
        (
            item
            for item in habit_service.list_habits(active_only=False)
            if item.name == name
        ),
        None,
    )
    if habit is None:
        raise RuntimeError(f'Could not find existing {name} habit')
    return habit


def _complete_on(habit_service: HabitService, habit_id: int, when: datetime) -> None:
    try:
        habit_service.complete_habit(habit_id, when=when)
    except HabitAlreadyCompletedForPeriod:
        pass


def _complete_daily_offsets(
    habit_service: HabitService,
    habit_id: int,
    reference_time: datetime,
    start_offset: int,
    end_offset: int,
) -> None:
    for day_offset in range(start_offset, end_offset - 1, -1):
        _complete_on(
            habit_service, habit_id, reference_time - timedelta(days=day_offset)
        )


def _iso_monday(reference_time: datetime) -> datetime:
    return reference_time - timedelta(days=reference_time.weekday())


def _complete_weekly_mondays(
    habit_service: HabitService, habit_id: int, reference_time: datetime
) -> None:
    monday = _iso_monday(reference_time)
    for week_offset in range(3, -1, -1):
        _complete_on(habit_service, habit_id, monday - timedelta(weeks=week_offset))


def _complete_weekly_calendar_edges(
    habit_service: HabitService, habit_id: int, reference_time: datetime
) -> None:
    monday = _iso_monday(reference_time)
    previous_sunday = (monday - timedelta(days=1)).replace(
        hour=23, minute=0, second=0, microsecond=0
    )
    current_monday_start = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    _complete_on(habit_service, habit_id, monday - timedelta(weeks=3))
    _complete_on(habit_service, habit_id, monday - timedelta(weeks=2))
    _complete_on(habit_service, habit_id, previous_sunday)
    _complete_on(habit_service, habit_id, current_monday_start)
