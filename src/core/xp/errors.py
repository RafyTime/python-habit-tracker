"""Domain exceptions for XP operations."""


class XPError(Exception):
    """Base exception for XP-related errors."""

    pass


class ActiveProfileRequired(XPError):
    """Raised when an operation requires an active profile but none is set."""

    def __init__(self) -> None:
        super().__init__(
            "No active profile. Use 'profile switch' to set an active profile."
        )
