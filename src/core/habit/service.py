"""Habit service for managing habits and completions."""

from collections.abc import Callable, Iterator
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Session, select
from sqlmodel.sql.expression import col

from src.core.analytics.dto import CompletionDTO, HabitDTO
from src.core.analytics.functions import longest_streak_for_habit
from src.core.habit.errors import (
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitNotFound,
)
from src.core.models import (
    Completion,
    Habit,
    Periodicity,
    Profile,
    XPEvent,
    require_persisted_id,
)
from src.core.profile.service import ProfileService

if TYPE_CHECKING:
    from src.core.xp.service import XPService


def _compute_period_key(when: datetime, periodicity: Periodicity) -> str:
    """
    Compute the period key for a given datetime and periodicity.

    Args:
        when: The datetime to compute the period for.
        periodicity: The periodicity type (DAILY or WEEKLY).

    Returns:
        Period key string: 'YYYY-MM-DD' for DAILY, 'YYYY-Www' for WEEKLY.
    """
    if periodicity == Periodicity.DAILY:
        return when.date().isoformat()
    elif periodicity == Periodicity.WEEKLY:
        # ISO week format: YYYY-Www
        year, week, _ = when.isocalendar()
        return f'{year}-W{week:02d}'
    else:
        raise ValueError(f'Unknown periodicity: {periodicity}')


class HabitService:
    """Service for habit management operations."""

    def __init__(
        self,
        session_factory: Callable[[], Iterator[Session]],
        xp_service: XPService | None = None,
    ) -> None:
        """
        Initialize the habit service.

        Args:
            session_factory: A callable that returns a generator yielding a Session.
                            Compatible with the get_session() function pattern.
            xp_service: Optional XP service for awarding XP on completions.
        """
        self._session_factory = session_factory
        self._xp_service = xp_service

    def _get_session(self) -> Session:
        """Get a database session from the factory."""
        return next(self._session_factory())

    def _get_active_profile(self, session: Session) -> Profile:
        """
        Get the currently active profile, ensuring one exists.

        Args:
            session: The database session to use.

        Returns:
            The active Profile instance.
        """
        return ProfileService(lambda: iter([session])).ensure_single_profile()

    def create_habit(
        self,
        name: str,
        periodicity: Periodicity,
        created_at: datetime | None = None,
    ) -> Habit:
        """
        Create a new habit for the active profile.

        Args:
            name: The name of the habit (will be normalized by trimming).
            periodicity: The periodicity type (DAILY or WEEKLY).
            created_at: Optional creation timestamp. Defaults to now.

        Returns:
            The created Habit instance.

        Raises:
            HabitAlreadyExists: If a habit with the same name already exists for the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError('Habit name cannot be empty')

        # Check for duplicates among active habits
        statement = select(Habit).where(
            Habit.profile_id == profile_id,
            Habit.name == normalized_name,
            col(Habit.is_active),
        )
        existing = session.exec(statement).first()

        if existing:
            raise HabitAlreadyExists(normalized_name)

        habit = Habit(
            profile_id=profile_id,
            name=normalized_name,
            periodicity=periodicity,
            created_at=created_at if created_at is not None else datetime.now(),
        )
        session.add(habit)
        session.commit()
        session.refresh(habit)

        return habit

    def list_habits(
        self,
        active_only: bool = True,
        periodicity: Periodicity | None = None,
    ) -> list[Habit]:
        """
        List habits for the active profile.

        Args:
            active_only: If True, only return active habits. Defaults to True.
            periodicity: Optional filter by periodicity type.

        Returns:
            A list of Habit instances matching the criteria.

        Raises:
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        statement = select(Habit).where(Habit.profile_id == profile.id)

        if active_only:
            statement = statement.where(col(Habit.is_active))

        if periodicity:
            statement = statement.where(Habit.periodicity == periodicity)

        return list(session.exec(statement.order_by(col(Habit.created_at))).all())

    def archive_habit(self, habit_id: int) -> Habit:
        """
        Archive a habit by setting is_active=False.

        Args:
            habit_id: The ID of the habit to archive.

        Returns:
            The archived Habit instance.

        Raises:
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile_id:
            raise HabitNotFound(habit_id=habit_id)

        habit.is_active = False
        session.add(habit)
        session.commit()
        session.refresh(habit)

        return habit

    def delete_habit(self, habit_id: int) -> str:
        """
        Permanently delete a habit and its dependent completion and XP records.

        Args:
            habit_id: The ID of the habit to delete.

        Returns:
            The name of the deleted habit.

        Raises:
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile_id:
            raise HabitNotFound(habit_id=habit_id)

        habit_name = habit.name

        """
        ADR: Here I had a couple options, whether to manually delete the completions and xp events or to use the cascade delete on the database (which was my first thought). Ended up going with manually deleting then as it's more explicit and easier to understand.
        """
        xp_events = list(
            session.exec(select(XPEvent).where(XPEvent.habit_id == habit_id))
        )
        completions = list(
            session.exec(select(Completion).where(Completion.habit_id == habit_id))
        )

        try:
            for event in xp_events:
                session.delete(event)
            for completion in completions:
                session.delete(completion)
            session.delete(habit)
            session.commit()
        except Exception:
            session.rollback()
            raise

        return habit_name

    def complete_habit(
        self, habit_id: int, when: datetime | None = None
    ) -> tuple[Completion, list[XPEvent]]:
        """
        Mark a habit as completed for the current period.

        Args:
            habit_id: The ID of the habit to complete.
            when: The datetime to use for completion (defaults to now).

        Returns:
            Tuple of (created Completion, list of newly awarded milestone XPEvents).

        Raises:
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
            HabitArchived: If the habit is archived.
            HabitAlreadyCompletedForPeriod: If the habit is already completed for this period.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile_id:
            raise HabitNotFound(habit_id=habit_id)

        if not habit.is_active:
            raise HabitArchived(habit_id)

        if when is None:
            when = datetime.now()

        period_key = _compute_period_key(when, habit.periodicity)

        # Check if already completed for this period
        statement = select(Completion).where(
            Completion.habit_id == habit_id,
            Completion.period_key == period_key,
        )
        existing = session.exec(statement).first()

        if existing:
            raise HabitAlreadyCompletedForPeriod(habit_id, period_key)

        # Create completion
        completion = Completion(
            habit_id=habit_id,
            completed_at=when,
            period_key=period_key,
        )
        session.add(completion)
        session.commit()
        session.refresh(completion)
        completion_id = require_persisted_id(completion.id, 'Completion')

        milestone_events: list[XPEvent] = []

        # Award XP if service is available
        if self._xp_service:
            self._xp_service.award_habit_completion(
                session, profile_id, habit_id, completion_id
            )
            session.commit()

            # Compute streak and award milestone XP for eligible targets
            completions = self.list_completions(habit_ids=[habit_id])
            habit_dto = HabitDTO(
                id=habit_id,
                name=habit.name,
                periodicity=habit.periodicity,
                created_at=habit.created_at,
                is_active=habit.is_active,
            )
            completion_dtos = [
                CompletionDTO(
                    habit_id=c.habit_id,
                    completed_at=c.completed_at,
                    period_key=c.period_key,
                )
                for c in completions
            ]
            streak = longest_streak_for_habit(habit_dto, completion_dtos)
            milestone_events = self._xp_service.award_milestone_xp(
                session, profile_id, habit_id, streak
            )
            if milestone_events:
                session.commit()

        return (completion, milestone_events)

    def get_due_habits(self, when: datetime | None = None) -> list[Habit]:
        """
        Get active habits that are due (not completed for the current period).

        Args:
            when: The datetime to use for period calculation (defaults to now).

        Returns:
            A list of Habit instances that are due.

        Raises:
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        if when is None:
            when = datetime.now()

        # Query active habits directly within the same session
        statement = select(Habit).where(
            Habit.profile_id == profile.id,
            col(Habit.is_active),
        )
        active_habits = list(
            session.exec(statement.order_by(col(Habit.created_at))).all()
        )

        due_habits = []
        for habit in active_habits:
            period_key = _compute_period_key(when, habit.periodicity)

            # Check if there's a completion for this period
            statement = select(Completion).where(
                Completion.habit_id == habit.id,
                Completion.period_key == period_key,
            )
            existing = session.exec(statement).first()

            if not existing:
                due_habits.append(habit)

        return due_habits

    def list_completions(self, habit_ids: list[int] | None = None) -> list[Completion]:
        """
        List completions for the active profile, optionally filtered by habit IDs.

        Args:
            habit_ids: Optional list of habit IDs to filter by. If None, returns all
                      completions for the active profile.

        Returns:
            A list of Completion instances for the active profile.

        Raises:
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        # Join Completion → Habit and filter by profile_id
        statement = (
            select(Completion)
            .join(Habit, col(Completion.habit_id) == col(Habit.id))
            .where(Habit.profile_id == profile.id)
        )

        if habit_ids is not None:
            statement = statement.where(col(Completion.habit_id).in_(habit_ids))

        return list(
            session.exec(statement.order_by(col(Completion.completed_at))).all()
        )
