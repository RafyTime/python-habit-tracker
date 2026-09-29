"""Convert persisted records to immutable Analytics inputs."""

from src.core.analytics.dto import CompletionDTO, HabitDTO
from src.core.models import Completion, Habit, require_persisted_id


def habit_to_dto(habit: Habit) -> HabitDTO:
    """Return the Analytics view of a persisted Habit."""
    return HabitDTO(
        id=require_persisted_id(habit.id, 'Habit'),
        name=habit.name,
        periodicity=habit.periodicity,
        created_at=habit.created_at,
        is_active=habit.is_active,
    )


def completion_to_dto(completion: Completion) -> CompletionDTO:
    """Return the Analytics view of a persisted Completion."""
    return CompletionDTO(
        habit_id=completion.habit_id,
        completed_at=completion.completed_at,
        period_key=completion.period_key,
    )
