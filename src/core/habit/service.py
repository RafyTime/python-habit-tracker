"""Habit service for managing habits and completions."""

from collections.abc import Callable, Iterator
from dataclasses import dataclass
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
    HabitArchivedNameExists,
    HabitNotFound,
)
from src.core.habit.names import identity_key
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


MAX_ICON_LENGTH = 8


@dataclass(frozen=True)
class HabitDeleteImpact:
    """Completion and XP records that a permanent delete will remove."""

    name: str
    completion_count: int
    xp_amount: int


def _normalize_icon(icon: str | None) -> str | None:
    if icon is None:
        return None
    if '\n' in icon or '\r' in icon:
        raise ValueError('Habit icon must be a single line')
    stripped = icon.strip()
    if not stripped:
        return None
    stripped = stripped.replace('\ufffd', '')
    if not stripped:
        raise ValueError('Habit icon is not valid')
    if len(stripped) > MAX_ICON_LENGTH:
        raise ValueError('Habit icon is too long')
    return stripped


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
        icon: str | None = None,
    ) -> Habit:
        """
        Create a new habit for the active profile.

        Args:
            name: The name of the habit (will be normalized by trimming).
            periodicity: The periodicity type (DAILY or WEEKLY).
            created_at: Optional creation timestamp. Defaults to now.
            icon: Optional short single-line Unicode icon.

        Returns:
            The created Habit instance.

        Raises:
            HabitAlreadyExists: If a habit with the same identity already exists.
            HabitArchivedNameExists: If an archived habit already uses that identity.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        display_name = name.strip()
        if not display_name:
            raise ValueError('Habit name cannot be empty')

        stored_icon = _normalize_icon(icon)
        conflict = self._conflicting_habit(session, profile_id, display_name)
        if conflict is not None:
            self._raise_name_conflict(conflict)

        habit = Habit(
            profile_id=profile_id,
            name=display_name,
            periodicity=periodicity,
            created_at=created_at if created_at is not None else datetime.now(),
            icon=stored_icon,
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

    def get_habit(self, selector: str) -> Habit:
        """Resolve a habit by numeric ID or exact normalized name.

        Name matching uses the shared identity key: outer whitespace is trimmed,
        underscores count as spaces, repeated whitespace collapses, and
        comparison is case-insensitive. Prefix and fuzzy matches are rejected.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')

        stripped = selector.strip()
        if stripped.isdigit():
            habit_id = int(stripped)
            habit = session.get(Habit, habit_id)
            if not habit or habit.profile_id != profile_id:
                raise HabitNotFound(habit_id=habit_id)
            return habit

        name_key = identity_key(stripped)
        for habit in session.exec(select(Habit).where(Habit.profile_id == profile_id)):
            if identity_key(habit.name) == name_key:
                return habit
        raise HabitNotFound(name=stripped)

    def _owned_habit(self, session: Session, profile_id: int, habit_id: int) -> Habit:
        habit = session.get(Habit, habit_id)
        if not habit or habit.profile_id != profile_id:
            raise HabitNotFound(habit_id=habit_id)
        return habit

    def _conflicting_habit(
        self,
        session: Session,
        profile_id: int,
        name: str,
        *,
        exclude_habit_id: int | None = None,
    ) -> Habit | None:
        name_key = identity_key(name)
        for existing in session.exec(
            select(Habit).where(Habit.profile_id == profile_id)
        ):
            if exclude_habit_id is not None and existing.id == exclude_habit_id:
                continue
            if identity_key(existing.name) == name_key:
                return existing
        return None

    def _raise_name_conflict(self, existing: Habit) -> None:
        if existing.is_active:
            raise HabitAlreadyExists(existing.name)
        raise HabitArchivedNameExists(existing.name)

    def update_habit(
        self,
        habit_id: int,
        *,
        name: str | None = None,
        icon: str | None = None,
        clear_icon: bool = False,
        include_archived: bool = False,
    ) -> Habit:
        """Update a habit's displayed name and/or icon.

        Periodicity is left unchanged so existing completion period keys
        keep their original daily or weekly meaning.
        """
        if clear_icon and icon is not None:
            raise ValueError(
                'Choose either a replacement icon or clearing the icon, not both.'
            )

        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')
        habit = self._owned_habit(session, profile_id, habit_id)

        if not habit.is_active and not include_archived:
            raise HabitArchived(habit_id)

        if name is not None:
            display_name = name.strip()
            if not display_name:
                raise ValueError('Habit name cannot be empty')
            conflict = self._conflicting_habit(
                session,
                profile_id,
                display_name,
                exclude_habit_id=habit_id,
            )
            if conflict is not None:
                raise HabitAlreadyExists(conflict.name)
            habit.name = display_name

        if clear_icon:
            habit.icon = None
        elif icon is not None:
            stored_icon = _normalize_icon(icon)
            if stored_icon is None:
                raise ValueError('Habit icon cannot be empty')
            habit.icon = stored_icon

        session.add(habit)
        session.commit()
        session.refresh(habit)
        return habit

    def restore_habit(self, habit_id: int) -> Habit:
        """Return an archived habit to active tracking without changing history."""
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')
        habit = self._owned_habit(session, profile_id, habit_id)

        if habit.is_active:
            return habit

        conflict = self._conflicting_habit(
            session,
            profile_id,
            habit.name,
            exclude_habit_id=habit_id,
        )
        if conflict is not None:
            raise HabitAlreadyExists(conflict.name)

        habit.is_active = True
        session.add(habit)
        session.commit()
        session.refresh(habit)
        return habit

    def streak_for_habit(self, habit: Habit) -> int:
        """Return the longest streak for a habit using the shared analytics rule."""
        habit_id = require_persisted_id(habit.id, 'Habit')
        completions = self.list_completions(habit_ids=[habit_id])
        return longest_streak_for_habit(
            HabitDTO(
                id=habit_id,
                name=habit.name,
                periodicity=habit.periodicity,
                created_at=habit.created_at,
                is_active=habit.is_active,
            ),
            [
                CompletionDTO(
                    habit_id=item.habit_id,
                    completed_at=item.completed_at,
                    period_key=item.period_key,
                )
                for item in completions
            ],
        )

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

    def _delete_impact(
        self, session: Session, habit: Habit
    ) -> tuple[HabitDeleteImpact, list[Completion], list[XPEvent]]:
        habit_id = require_persisted_id(habit.id, 'Habit')
        completions = list(
            session.exec(select(Completion).where(Completion.habit_id == habit_id))
        )
        xp_events = list(
            session.exec(select(XPEvent).where(XPEvent.habit_id == habit_id))
        )
        impact = HabitDeleteImpact(
            name=habit.name,
            completion_count=len(completions),
            xp_amount=sum(event.amount for event in xp_events),
        )
        return impact, completions, xp_events

    def preview_delete(self, habit_id: int) -> HabitDeleteImpact:
        """Return the completion and XP impact of deleting a habit without changing data."""
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')
        habit = self._owned_habit(session, profile_id, habit_id)
        impact, _, _ = self._delete_impact(session, habit)
        return impact

    def delete_habit(self, habit_id: int) -> HabitDeleteImpact:
        """
        Permanently delete a habit and its dependent completion and XP records.

        Args:
            habit_id: The ID of the habit to delete.

        Returns:
            The name, completion count, and XP amount that were removed.

        Raises:
            HabitNotFound: If the habit is not found or doesn't belong to the active profile.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        profile_id = require_persisted_id(profile.id, 'Active profile')
        habit = self._owned_habit(session, profile_id, habit_id)
        impact, completions, xp_events = self._delete_impact(session, habit)

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

        return impact

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

            streak = self.streak_for_habit(habit)
            milestone_events = self._xp_service.award_milestone_xp(
                session, profile_id, habit_id, streak
            )
            if milestone_events:
                session.commit()

        session.refresh(completion)
        for event in milestone_events:
            session.refresh(event)
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
