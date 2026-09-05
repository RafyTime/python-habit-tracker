"""Analytics module for habit tracking analytics."""

from src.core.analytics.dto import (
    CompletionDTO,
    CurrentStreakDTO,
    HabitDTO,
    LongestStreakDTO,
)
from src.core.analytics.functions import (
    current_streak_for_habit,
    filter_habits_by_archived_inclusion,
    filter_habits_by_periodicity,
    list_all_habits,
    longest_streak_across_habits,
    longest_streak_for_habit,
)

__all__ = [
    'CompletionDTO',
    'CurrentStreakDTO',
    'HabitDTO',
    'LongestStreakDTO',
    'current_streak_for_habit',
    'filter_habits_by_archived_inclusion',
    'filter_habits_by_periodicity',
    'list_all_habits',
    'longest_streak_across_habits',
    'longest_streak_for_habit',
]
