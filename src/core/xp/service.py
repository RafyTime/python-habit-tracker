"""XP service for managing experience points and levels."""

from collections.abc import Callable, Generator
from math import floor

from sqlmodel import Session, func, select

from src.core.models import AppState, Profile, XPEvent
from src.core.xp.errors import ActiveProfileRequired


class XPService:
    """Service for XP management operations."""

    def __init__(self, session_factory: Callable[[], Generator[Session]]) -> None:
        """
        Initialize the XP service.

        Args:
            session_factory: A callable that returns a generator yielding a Session.
                            Compatible with the get_session() function pattern.
        """
        self._session_factory = session_factory

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

    def award_habit_completion(
        self, session: Session, profile_id: int, habit_id: int, completion_id: int
    ) -> XPEvent:
        """
        Award XP for a habit completion (idempotent).

        Args:
            session: The database session to use (must be the same as the completion).
            profile_id: The ID of the profile receiving XP.
            habit_id: The ID of the habit that was completed.
            completion_id: The ID of the completion (used for idempotency).

        Returns:
            The XPEvent instance (existing or newly created).
        """
        # Check if XP already awarded for this completion
        existing = session.exec(
            select(XPEvent).where(XPEvent.completion_id == completion_id)
        ).first()

        if existing:
            return existing

        # Award XP
        xp_event = XPEvent(
            profile_id=profile_id,
            amount=1,
            reason='HABIT_COMPLETION',
            habit_id=habit_id,
            completion_id=completion_id,
        )
        session.add(xp_event)
        session.commit()
        session.refresh(xp_event)

        return xp_event

    def get_total_xp(self, session: Session, profile_id: int) -> int:
        """
        Get the total XP for a profile.

        Args:
            session: The database session to use.
            profile_id: The ID of the profile.

        Returns:
            The total XP (0 if no events exist).
        """
        result = session.exec(
            select(func.sum(XPEvent.amount)).where(XPEvent.profile_id == profile_id)
        ).one()

        return int(result) if result is not None else 0

    def compute_level(self, total_xp: int) -> int:
        """
        Compute the level from total XP.

        Formula: level = 1 + floor(total_xp / 10)

        Args:
            total_xp: The total XP amount.

        Returns:
            The computed level.
        """
        return 1 + floor(total_xp / 10)

    def compute_level_progress(self, total_xp: int) -> tuple[int, int, int]:
        """
        Compute level progress information.

        Args:
            total_xp: The total XP amount.

        Returns:
            A tuple of (level, xp_into_level, xp_to_next_level).
        """
        level = self.compute_level(total_xp)
        xp_into_level = total_xp % 10
        xp_to_next_level = 10 - xp_into_level

        return (level, xp_into_level, xp_to_next_level)

    def get_total_xp_for_active_profile(self) -> int:
        """
        Convenience method to get total XP for the active profile.

        Returns:
            The total XP for the active profile.

        Raises:
            ActiveProfileRequired: If no profile is active.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        return self.get_total_xp(session, profile.id)

    def get_level_progress_for_active_profile(self) -> tuple[int, int, int]:
        """
        Convenience method to get level progress for the active profile.

        Returns:
            A tuple of (level, xp_into_level, xp_to_next_level).

        Raises:
            ActiveProfileRequired: If no profile is active.
        """
        session = self._get_session()
        profile = self._get_active_profile(session)
        total_xp = self.get_total_xp(session, profile.id)
        return self.compute_level_progress(total_xp)
