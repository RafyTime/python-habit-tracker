"""Manage the tracker's one display name and home preference."""

from collections.abc import Callable, Iterator

from sqlmodel import Session, select

from src.core.models import AfterAction, Profile


class ProfileService:
    """Read or update the single persisted profile."""

    def __init__(self, session_factory: Callable[[], Iterator[Session]]) -> None:
        """Accept the session iterator used by the database module."""
        self._session_factory = session_factory

    DEFAULT_DISPLAY_NAME = 'User'

    def _get_session(self) -> Session:
        """Get a database session from the factory."""
        return next(self._session_factory())

    def ensure_single_profile(self) -> Profile:
        """Return the persisted profile, creating the default on a fresh database."""
        session = self._get_session()
        profile = session.exec(select(Profile)).first()
        if profile is not None:
            return profile
        profile = Profile(id=1, display_name=self.DEFAULT_DISPLAY_NAME)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile

    def update_display_name(self, display_name: str) -> Profile:
        """Set a nonempty display name on the single profile."""
        normalized = display_name.strip()
        if not normalized:
            raise ValueError('Display name cannot be empty')

        session = self._get_session()
        profile = self.ensure_single_profile()
        # Re-load in this session in case ensure used a prior session handle.
        profile = session.get(Profile, profile.id)
        if profile is None:
            raise RuntimeError('Single profile missing after ensure')

        profile.display_name = normalized
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile

    def update_after_action(self, after_action: AfterAction) -> Profile:
        """Update the single profile's after-action preference."""
        session = self._get_session()
        profile = self.ensure_single_profile()
        profile = session.get(Profile, profile.id)
        if profile is None:
            raise RuntimeError('Single profile missing after ensure')

        profile.after_action = after_action
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile
