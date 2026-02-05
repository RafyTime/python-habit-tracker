"""Pure analytics functions operating on DTOs."""

from collections.abc import Sequence
from datetime import date

from src.core.analytics.dto import CompletionDTO, HabitDTO, LongestStreakDTO
from src.core.models import Periodicity


def list_all_habits(habits: Sequence[HabitDTO]) -> list[HabitDTO]:
    """
    List all habits (identity function for explicit API).

    Args:
        habits: Sequence of habit DTOs.

    Returns:
        List of all habit DTOs.
    """
    return list(habits)


def filter_habits_by_periodicity(
    habits: Sequence[HabitDTO], periodicity: Periodicity
) -> list[HabitDTO]:
    """
    Filter habits by periodicity type.

    Args:
        habits: Sequence of habit DTOs.
        periodicity: Periodicity type to filter by.

    Returns:
        List of habit DTOs matching the periodicity.
    """
    return [h for h in habits if h.periodicity == periodicity]


def _parse_period_key_to_ordinal(period_key: str, periodicity: Periodicity) -> int:
    """
    Parse a period key into an integer timeline index (ordinal).

    Args:
        period_key: Period key string (YYYY-MM-DD for DAILY, YYYY-Www for WEEKLY).
        periodicity: Periodicity type.

    Returns:
        Integer ordinal representing the period.
    """
    if periodicity == Periodicity.DAILY:
        # Parse YYYY-MM-DD and convert to ordinal
        period_date = date.fromisoformat(period_key)
        return period_date.toordinal()
    elif periodicity == Periodicity.WEEKLY:
        # Parse YYYY-Www and convert to ordinal of the Monday of that week
        year_str, week_str = period_key.split('-W')
        year = int(year_str)
        week = int(week_str)
        # Get the Monday of the ISO week
        monday = date.fromisocalendar(year, week, 1)
        return monday.toordinal()
    else:
        raise ValueError(f'Unknown periodicity: {periodicity}')


def _get_consecutive_step(periodicity: Periodicity) -> int:
    """
    Get the step size for consecutive periods.

    Args:
        periodicity: Periodicity type.

    Returns:
        Step size (1 for DAILY, 7 for WEEKLY).
    """
    if periodicity == Periodicity.DAILY:
        return 1
    elif periodicity == Periodicity.WEEKLY:
        return 7
    else:
        raise ValueError(f'Unknown periodicity: {periodicity}')


def longest_streak_for_habit(
    habit: HabitDTO, completions: Sequence[CompletionDTO]
) -> int:
    """
    Calculate the longest streak for a specific habit.

    Args:
        habit: The habit DTO.
        completions: Sequence of completion DTOs (will be filtered by habit_id).

    Returns:
        Length of the longest streak (0 if no completions).
    """
    # Filter completions for this habit
    habit_completions = [c for c in completions if c.habit_id == habit.id]

    if not habit_completions:
        return 0

    # Parse period keys to ordinals and deduplicate
    period_ordinals = set()
    for completion in habit_completions:
        try:
            ordinal = _parse_period_key_to_ordinal(
                completion.period_key, habit.periodicity
            )
            period_ordinals.add(ordinal)
        except (ValueError, KeyError):
            # Skip invalid period keys
            continue

    if not period_ordinals:
        return 0

    # Sort ordinals
    sorted_ordinals = sorted(period_ordinals)
    step = _get_consecutive_step(habit.periodicity)

    # Find the longest consecutive run
    max_streak = 1
    current_streak = 1

    for i in range(1, len(sorted_ordinals)):
        if sorted_ordinals[i] == sorted_ordinals[i - 1] + step:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1

    return max_streak


def longest_streak_across_habits(
    habits: Sequence[HabitDTO], completions: Sequence[CompletionDTO]
) -> LongestStreakDTO:
    """
    Find the longest streak across all habits.

    Args:
        habits: Sequence of habit DTOs.
        completions: Sequence of completion DTOs.

    Returns:
        LongestStreakDTO with the best streak information.
        If no habits exist or no completions, returns length 0 with None fields.
    """
    if not habits:
        return LongestStreakDTO(
            length=0, habit_id=None, habit_name=None, periodicity=None
        )

    best_streak = 0
    best_habit: HabitDTO | None = None

    for habit in habits:
        streak = longest_streak_for_habit(habit, completions)
        if streak > best_streak:
            best_streak = streak
            best_habit = habit
        elif streak == best_streak and best_habit is not None:
            # Tie-breaking: prefer lower habit_id for determinism
            if habit.id < best_habit.id:
                best_habit = habit

    if best_habit is None or best_streak == 0:
        return LongestStreakDTO(
            length=0, habit_id=None, habit_name=None, periodicity=None
        )

    return LongestStreakDTO(
        length=best_streak,
        habit_id=best_habit.id,
        habit_name=best_habit.name,
        periodicity=best_habit.periodicity,
    )
