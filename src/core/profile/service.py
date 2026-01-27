"""Profile service for managing user profiles and active profile state."""

from collections.abc import Callable, Generator

from sqlmodel import Session, select

from src.core.models import AppState, Profile
from src.core.profile.errors import ProfileAlreadyExists, ProfileNotFound


class ProfileService:
    """Service for profile management operations."""

    def __init__(self, session_factory: Callable[[], Generator[Session]]) -> None:
        """
        Initialize the profile service.

        Args:
            session_factory: A callable that returns a generator yielding a Session.
                            Compatible with the get_session() function pattern.
        """
        self._session_factory = session_factory

    def _get_session(self) -> Session:
        """Get a database session from the factory."""
        return next(self._session_factory())

    def create_profile(self, username: str) -> Profile:
        """
        Create a new profile with the given username.

        Args:
            username: The username for the new profile (will be normalized to lowercase).

        Returns:
            The created Profile instance.

        Raises:
            ProfileAlreadyExists: If a profile with the given username already exists.
        """
        session = self._get_session()
        normalized_username = username.lower()

        # Check if profile already exists
        statement = select(Profile).where(Profile.username == normalized_username)
        existing = session.exec(statement).first()

        if existing:
            raise ProfileAlreadyExists(normalized_username)

        # Create profile
        profile = Profile(username=normalized_username)
        session.add(profile)
        session.commit()
        session.refresh(profile)

        return profile

    def list_profiles(self) -> list[Profile]:
        """
        List all available profiles.

        Returns:
            A list of all Profile instances, ordered by creation time.
        """
        session = self._get_session()
        return list(session.exec(select(Profile)).all())

    def get_active_profile(self) -> Profile | None:
        """
        Get the currently active profile.

        Returns:
            The active Profile instance, or None if no profile is active.
        """
        session = self._get_session()
        state = session.get(AppState, 1)
        if state and state.active_profile_id:
            return session.get(Profile, state.active_profile_id)
        return None

    def switch_active_profile(self, username: str) -> Profile:
        """
        Switch the active profile to the specified username.

        Args:
            username: The username of the profile to switch to (case-insensitive).

        Returns:
            The Profile instance that is now active.

        Raises:
            ProfileNotFound: If no profile with the given username exists.
        """
        session = self._get_session()
        normalized_username = username.lower()

        profile = session.exec(
            select(Profile).where(Profile.username == normalized_username)
        ).first()

        if not profile:
            raise ProfileNotFound(normalized_username)

        # Update or create AppState
        state = session.get(AppState, 1)
        if not state:
            state = AppState(id=1, active_profile_id=profile.id)
            session.add(state)
        else:
            state.active_profile_id = profile.id
            session.add(state)
        session.commit()

        return profile

    def delete_profile(self, username: str) -> None:
        """
        Delete a profile by username.

        If the deleted profile is currently active, the active profile state will be cleared.

        Args:
            username: The username of the profile to delete (case-insensitive).

        Raises:
            ProfileNotFound: If no profile with the given username exists.
        """
        session = self._get_session()
        normalized_username = username.lower()

        profile = session.exec(
            select(Profile).where(Profile.username == normalized_username)
        ).first()

        if not profile:
            raise ProfileNotFound(normalized_username)

        # Check if this is the active profile
        state = session.get(AppState, 1)
        is_active = state and state.active_profile_id == profile.id

        # If deleting active profile, clear state
        if is_active:
            if state:
                state.active_profile_id = None
                session.add(state)

        session.delete(profile)
        session.commit()
