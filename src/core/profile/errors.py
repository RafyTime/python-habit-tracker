"""Domain exceptions for profile operations."""


class ProfileError(Exception):
    """Base exception for profile-related errors."""

    pass


class ProfileAlreadyExists(ProfileError):
    """Raised when attempting to create a profile with an existing username."""

    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Profile '{username}' already exists")


class ProfileNotFound(ProfileError):
    """Raised when a profile cannot be found."""

    def __init__(self, username: str) -> None:
        self.username = username
        super().__init__(f"Profile '{username}' not found")
