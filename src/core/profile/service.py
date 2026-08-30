"""Profile service for managing user profiles and active profile state."""

from collections.abc import Callable, Iterator

from sqlmodel import Session, select
from sqlmodel.sql.expression import col

from src.core.models import AfterAction, AppState, Profile
from src.core.profile.errors import ProfileAlreadyExists, ProfileNotFound


class ProfileService:
    """Service for profile management operations."""

    def __init__(self, session_factory: Callable[[], Iterator[Session]]) -> None:
        """
        Initialize the profile service.

        Args:
            session_factory: A callable that returns a generator yielding a Session.
                            Compatible with the get_session() function pattern.
        """
        self._session_factory = session_factory

    DEFAULT_DISPLAY_NAME = 'User'

    def _get_session(self) -> Session:
        """Get a database session from the factory."""
        return next(self._session_factory())

    def ensure_single_profile(self) -> Profile:
        """
        Ensure one usable profile is active.

        On a fresh database, creates a default profile. On legacy multi-profile
        data, activates the current active profile, else the legacy primary
        profile, else the earliest profile by creation time. Other legacy
        profiles are left intact so their data is not discarded.
        """
        session = self._get_session()
        profiles = list(
            session.exec(select(Profile).order_by(col(Profile.created_at))).all()
        )

        if not profiles:
            profile = Profile(username=self.DEFAULT_DISPLAY_NAME)
            session.add(profile)
            session.commit()
            session.refresh(profile)
            state = AppState(id=1, active_profile_id=profile.id)
            session.add(state)
            session.commit()
            session.refresh(profile)
            return profile

        state = session.get(AppState, 1)
        chosen: Profile | None = None
        if state and state.active_profile_id is not None:
            chosen = session.get(Profile, state.active_profile_id)

        if chosen is None:
            chosen = next(
                (p for p in profiles if p.username == 'primary'),
                profiles[0],
            )

        if not state:
            state = AppState(id=1, active_profile_id=chosen.id)
            session.add(state)
        elif state.active_profile_id != chosen.id:
            state.active_profile_id = chosen.id
            session.add(state)
        session.commit()
        session.refresh(chosen)
        return chosen

    def update_display_name(self, display_name: str) -> Profile:
        """
        Update the single profile's display name.

        Args:
            display_name: The new display name (whitespace-stripped).

        Returns:
            The updated Profile instance.

        Raises:
            ValueError: If the display name is empty after stripping.
        """
        normalized = display_name.strip()
        if not normalized:
            raise ValueError('Display name cannot be empty')

        session = self._get_session()
        profile = self.ensure_single_profile()
        # Re-load in this session in case ensure used a prior session handle.
        profile = session.get(Profile, profile.id)
        if profile is None:
            raise RuntimeError('Single profile missing after ensure')

        profile.username = normalized
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

    def get_active_profile(self) -> Profile:
        """
        Get the currently active profile, ensuring one exists.

        Returns:
            The active Profile instance.
        """
        return self.ensure_single_profile()

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
