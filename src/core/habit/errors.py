"""Domain exceptions for habit operations."""


class HabitError(Exception):
    """Base exception for habit-related errors."""

    pass


class ActiveProfileRequired(HabitError):
    """Raised when an operation requires an active profile but none is set."""

    def __init__(self) -> None:
        super().__init__(
            "No active profile. Use 'profile switch' to set an active profile."
        )


class HabitNotFound(HabitError):
    """Raised when a habit cannot be found."""

    def __init__(self, habit_id: int | None = None, name: str | None = None) -> None:
        if habit_id is not None:
            message = f'Habit with ID {habit_id} not found'
        elif name is not None:
            message = f"Habit '{name}' not found"
        else:
            message = 'Habit not found'
        super().__init__(message)
        self.habit_id = habit_id
        self.name = name


class HabitAlreadyExists(HabitError):
    """Raised when attempting to create a habit with a name that already exists for the active profile."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Habit '{name}' already exists for this profile")


class HabitArchived(HabitError):
    """Raised when attempting to complete an archived habit."""

    def __init__(self, habit_id: int) -> None:
        self.habit_id = habit_id
        super().__init__(f'Habit {habit_id} is archived and cannot be completed')


class HabitAlreadyCompletedForPeriod(HabitError):
    """Raised when attempting to complete a habit twice in the same period."""

    def __init__(self, habit_id: int, period_key: str) -> None:
        self.habit_id = habit_id
        self.period_key = period_key
        super().__init__(
            f"Habit {habit_id} has already been completed for period '{period_key}'"
        )
