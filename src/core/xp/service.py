"""Award Completion and Milestone XP and calculate Levels."""

from collections.abc import Callable, Iterator
from math import floor

from sqlmodel import Session, func, select
from sqlmodel.sql.expression import desc

from src.core.models import Profile, XPEvent, require_persisted_id
from src.core.profile.service import ProfileService

# Each Habit claims each five-XP Milestone at most once.
MILESTONE_STREAK_TARGETS: tuple[int, ...] = (3, 7, 14, 30)
MILESTONE_BONUS_XP: int = 5


class XPService:
    """Manage persisted XP events for the single profile."""

    def __init__(self, session_factory: Callable[[], Iterator[Session]]) -> None:
        """Accept the session iterator used by the database module."""
        self._session_factory = session_factory

    def _get_session(self) -> Session:
        """Get a database session from the factory."""
        return next(self._session_factory())

    def _get_profile(self, session: Session) -> Profile:
        """Get the single profile in this session, creating it if needed."""
        return ProfileService(lambda: iter([session])).ensure_single_profile()

    def award_habit_completion(
        self, session: Session, profile_id: int, habit_id: int, completion_id: int
    ) -> XPEvent:
        """Award one XP once for a persisted Completion."""
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

    def award_milestone_xp(
        self,
        session: Session,
        profile_id: int,
        habit_id: int,
        streak_length: int,
    ) -> list[XPEvent]:
        """Claim each reached Milestone once for this Habit identity."""
        newly_awarded: list[XPEvent] = []

        for target in MILESTONE_STREAK_TARGETS:
            if streak_length < target:
                continue

            reason = f'MILESTONE_STREAK_{target}'
            existing = session.exec(
                select(XPEvent).where(
                    XPEvent.profile_id == profile_id,
                    XPEvent.habit_id == habit_id,
                    XPEvent.reason == reason,
                )
            ).first()

            if existing:
                continue

            xp_event = XPEvent(
                profile_id=profile_id,
                amount=MILESTONE_BONUS_XP,
                reason=reason,
                habit_id=habit_id,
                completion_id=None,
            )
            session.add(xp_event)
            session.commit()
            session.refresh(xp_event)
            newly_awarded.append(xp_event)

        return newly_awarded

    def get_total_xp(self, session: Session, profile_id: int) -> int:
        """Sum the profile's retained XP events."""
        result = session.exec(
            select(func.sum(XPEvent.amount)).where(XPEvent.profile_id == profile_id)
        ).one()

        return int(result) if result is not None else 0

    def compute_level(self, total_xp: int) -> int:
        """Return Level 1 plus one Level for each ten XP."""
        return 1 + floor(total_xp / 10)

    def compute_level_progress(self, total_xp: int) -> tuple[int, int, int]:
        """Return Level, XP earned within it, and XP needed for the next Level."""
        level = self.compute_level(total_xp)
        xp_into_level = total_xp % 10
        xp_to_next_level = 10 - xp_into_level

        return (level, xp_into_level, xp_to_next_level)

    def get_total_xp_for_habit(self, habit_id: int) -> int:
        """Return retained XP earned by one habit for the profile."""
        session = self._get_session()
        profile = self._get_profile(session)
        profile_id = require_persisted_id(profile.id, 'Profile')
        result = session.exec(
            select(func.sum(XPEvent.amount)).where(
                XPEvent.profile_id == profile_id,
                XPEvent.habit_id == habit_id,
            )
        ).one()
        return int(result) if result is not None else 0

    def get_total_xp_for_profile(self) -> int:
        """Return the single profile's total retained XP."""
        session = self._get_session()
        profile = self._get_profile(session)
        profile_id = require_persisted_id(profile.id, 'Profile')
        return self.get_total_xp(session, profile_id)

    def get_level_progress_for_profile(self) -> tuple[int, int, int]:
        """Return the single profile's Level progress."""
        session = self._get_session()
        profile = self._get_profile(session)
        profile_id = require_persisted_id(profile.id, 'Profile')
        total_xp = self.get_total_xp(session, profile_id)
        return self.compute_level_progress(total_xp)

    def list_recent_events_for_profile(self, limit: int = 10) -> list[XPEvent]:
        """Return recent XP events for the profile, newest first."""
        session = self._get_session()
        profile = self._get_profile(session)
        profile_id = require_persisted_id(profile.id, 'Profile')
        statement = (
            select(XPEvent)
            .where(XPEvent.profile_id == profile_id)
            .order_by(desc(XPEvent.awarded_at), desc(XPEvent.id))
            .limit(limit)
        )
        return list(session.exec(statement))
