"""Habit service for managing habits and completions."""

from collections.abc import Callable, Generator
from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Session, select
from sqlmodel.sql.expression import col

from src.core.habit.errors import (
    ActiveProfileRequired,
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitNotFound,
)
from src.core.models import AppState, Completion, Habit, Periodicity, Profile

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
        return f"{year}-W{week:02d}"
    else:
        raise ValueError(f"Unknown periodicity: {periodicity}")


class HabitService:
    """Service for habit management operations."""

    def __init__(
        self,
        session_factory: Callable[[], Generator[Session]],
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
        Get the currently active profile.

        Args:
            session: The database session to use.

        Returns:
            The active Profile instance.

        Raises:
            ActiveProfileRequired: If no profile is active.
        """
        state = session.get(AppState, 1)
        if not state or not state.active_profile_id:
            raise ActiveProfileRequired()

        profile = session.get(Profile, state.active_profile_id)
        if not profile:
            raise ActiveProfileRequired()

        return profile

    def create_habit(self, name: str, periodicity: Periodicity) -> Habit:
        """
        Create a new habit for the active profile.

        Args:
            name: The name of the habit (will be normalized by trimming).
            periodicity: The periodicity type (DAILY or WEEKLY).

        Returns:
            The created Habit instance.

        Raises:
            ActiveProfileRequired: If no profile is active.
            HabitAlreadyExists: If a habit with the same name already exists for the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Habit name cannot be empty")

        # Check for duplicates among active habits
        statement = select(Habit).where(
            Habit.profile_id == profile.id,
            Habit.name == normalized_name,
            Habit.is_active == True,  # noqa: E712
        )
        existing = session.exec(statement).first()

        if existing:
            raise HabitAlreadyExists(normalized_name)

        # Create habit
        habit = Habit(
            profile_id=profile.id,
            name=normalized_name,
            periodicity=periodicity,
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
            ActiveProfileRequired: If no profile is active.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        statement = select(Habit).where(Habit.profile_id == profile.id)

        if active_only:
            statement = statement.where(Habit.is_active == True)  # noqa: E712

        if periodicity:
            statement = statement.where(Habit.periodicity == periodicity)

        return list(session.exec(statement.order_by(Habit.created_at)).all())

    def archive_habit(self, habit_id: int) -> Habit:
        """
        Archive a habit by setting is_active=False.

        Args:
            habit_id: The ID of the habit to archive.

        Returns:
            The archived Habit instance.

        Raises:
            ActiveProfileRequired: If no profile is active.
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile.id:
            raise HabitNotFound(habit_id=habit_id)

        habit.is_active = False
        session.add(habit)
        session.commit()
        session.refresh(habit)

        return habit

    def complete_habit(
        self, habit_id: int, when: datetime | None = None
    ) -> Completion:
        """
        Mark a habit as completed for the current period.

        Args:
            habit_id: The ID of the habit to complete.
            when: The datetime to use for completion (defaults to now).

        Returns:
            The created Completion instance.

        Raises:
            ActiveProfileRequired: If no profile is active.
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
            HabitArchived: If the habit is archived.
            HabitAlreadyCompletedForPeriod: If the habit is already completed for this period.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile.id:
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

        # Award XP if service is available
        if self._xp_service:
            self._xp_service.award_habit_completion(
                session, profile.id, habit_id, completion.id
            )
            session.commit()

        return completion

    def get_due_habits(self, when: datetime | None = None) -> list[Habit]:
        """
        Get active habits that are due (not completed for the current period).

        Args:
            when: The datetime to use for period calculation (defaults to now).

        Returns:
            A list of Habit instances that are due.

        Raises:
            ActiveProfileRequired: If no profile is active.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        if when is None:
            when = datetime.now()

        # Query active habits directly within the same session
        statement = select(Habit).where(
            Habit.profile_id == profile.id,
            Habit.is_active == True,  # noqa: E712
        )
        active_habits = list(session.exec(statement.order_by(Habit.created_at)).all())

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
            ActiveProfileRequired: If no profile is active.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)

        # Join Completion → Habit and filter by profile_id
        statement = (
            select(Completion)
            .join(Habit, Completion.habit_id == Habit.id)
            .where(Habit.profile_id == profile.id)
        )

        if habit_ids is not None:
            statement = statement.where(col(Completion.habit_id).in_(habit_ids))

        return list(session.exec(statement.order_by(Completion.completed_at)).all())
