"""Pure unit tests for analytics functions (no database required)."""

from datetime import datetime

from src.core.analytics.dto import CompletionDTO, HabitDTO
from src.core.analytics.functions import (
    filter_habits_by_periodicity,
    list_all_habits,
    longest_streak_across_habits,
    longest_streak_for_habit,
)
from src.core.models import Periodicity


def test_list_all_habits():
    """Test that list_all_habits returns all habits."""
    habits = [
        HabitDTO(
            id=1,
            name='Habit 1',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
        HabitDTO(
            id=2,
            name='Habit 2',
            periodicity=Periodicity.WEEKLY,
            created_at=datetime.now(),
            is_active=True,
        ),
    ]
    result = list_all_habits(habits)
    assert result == habits
    assert len(result) == 2


def test_filter_habits_by_periodicity():
    """Test filtering habits by periodicity."""
    habits = [
        HabitDTO(
            id=1,
            name='Daily Habit',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
        HabitDTO(
            id=2,
            name='Weekly Habit',
            periodicity=Periodicity.WEEKLY,
            created_at=datetime.now(),
            is_active=True,
        ),
        HabitDTO(
            id=3,
            name='Another Daily',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
    ]

    daily_habits = filter_habits_by_periodicity(habits, Periodicity.DAILY)
    assert len(daily_habits) == 2
    assert all(h.periodicity == Periodicity.DAILY for h in daily_habits)
    assert daily_habits[0].name == 'Daily Habit'
    assert daily_habits[1].name == 'Another Daily'

    weekly_habits = filter_habits_by_periodicity(habits, Periodicity.WEEKLY)
    assert len(weekly_habits) == 1
    assert weekly_habits[0].name == 'Weekly Habit'


def test_longest_streak_for_habit_no_completions():
    """Test longest streak for habit with no completions returns 0."""
    habit = HabitDTO(
        id=1,
        name='Test Habit',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions: list[CompletionDTO] = []
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 0


def test_longest_streak_for_habit_single_completion():
    """Test longest streak for habit with single completion returns 1."""
    habit = HabitDTO(
        id=1,
        name='Test Habit',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 1


def test_longest_streak_for_habit_consecutive_days():
    """Test longest streak with consecutive daily completions."""
    habit = HabitDTO(
        id=1,
        name='Daily Habit',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 3),
            period_key='2025-01-03',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 3


def test_longest_streak_for_habit_broken_streak():
    """Test longest streak picks max run when streak is broken."""
    habit = HabitDTO(
        id=1,
        name='Daily Habit',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 4),  # Skip day 3
            period_key='2025-01-04',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 5),
            period_key='2025-01-05',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 6),
            period_key='2025-01-06',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 3  # Max of [1,2] (2) and [4,5,6] (3)


def test_longest_streak_for_habit_duplicates():
    """Test that duplicates in input are handled correctly."""
    habit = HabitDTO(
        id=1,
        name='Daily Habit',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),  # Duplicate
            period_key='2025-01-01',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 2  # Should deduplicate and still find streak of 2


def test_longest_streak_for_habit_weekly():
    """Test longest streak calculation for weekly habits."""
    habit = HabitDTO(
        id=1,
        name='Weekly Habit',
        periodicity=Periodicity.WEEKLY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 6),  # Week 1 (Monday is Jan 6)
            period_key='2025-W01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 13),  # Week 2
            period_key='2025-W02',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 27),  # Week 4 (skip week 3)
            period_key='2025-W04',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    assert streak == 2  # Max of [W01, W02] (2) and [W04] (1)


def test_longest_streak_weekly_across_year_boundary():
    """Test weekly streak calculation across year boundary."""
    habit = HabitDTO(
        id=1,
        name='Weekly Habit',
        periodicity=Periodicity.WEEKLY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 12, 23),  # Week 52 of 2025
            period_key='2025-W52',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 12, 30),  # Week 1 of 2026 (ISO week)
            period_key='2026-W01',
        ),
    ]
    streak = longest_streak_for_habit(habit, completions)
    # Should recognize consecutive weeks even across year boundary
    # Week 52 of 2025 ends Dec 28, Week 1 of 2026 starts Dec 29
    # These should be consecutive (7 days apart)
    assert streak == 2


def test_longest_streak_for_habit_filters_by_habit_id():
    """Test that completions for other habits are ignored."""
    habit1 = HabitDTO(
        id=1,
        name='Habit 1',
        periodicity=Periodicity.DAILY,
        created_at=datetime.now(),
        is_active=True,
    )
    completions = [
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=2,  # Different habit
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
    ]
    streak = longest_streak_for_habit(habit1, completions)
    assert streak == 2  # Only counts completions for habit 1


def test_longest_streak_across_habits_no_habits():
    """Test longest streak across habits with no habits returns length 0."""
    habits: list[HabitDTO] = []
    completions: list[CompletionDTO] = []
    result = longest_streak_across_habits(habits, completions)
    assert result.length == 0
    assert result.habit_id is None
    assert result.habit_name is None
    assert result.periodicity is None


def test_longest_streak_across_habits_no_completions():
    """Test longest streak across habits with habits but no completions."""
    habits = [
        HabitDTO(
            id=1,
            name='Habit 1',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
    ]
    completions: list[CompletionDTO] = []
    result = longest_streak_across_habits(habits, completions)
    assert result.length == 0
    assert result.habit_id is None
    assert result.habit_name is None
    assert result.periodicity is None


def test_longest_streak_across_habits_picks_best():
    """Test that longest streak across habits picks the habit with longest streak."""
    habits = [
        HabitDTO(
            id=1,
            name='Habit 1',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
        HabitDTO(
            id=2,
            name='Habit 2',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
    ]
    completions = [
        # Habit 1: streak of 2
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        # Habit 2: streak of 3
        CompletionDTO(
            habit_id=2,
            completed_at=datetime(2025, 1, 5),
            period_key='2025-01-05',
        ),
        CompletionDTO(
            habit_id=2,
            completed_at=datetime(2025, 1, 6),
            period_key='2025-01-06',
        ),
        CompletionDTO(
            habit_id=2,
            completed_at=datetime(2025, 1, 7),
            period_key='2025-01-07',
        ),
    ]
    result = longest_streak_across_habits(habits, completions)
    assert result.length == 3
    assert result.habit_id == 2
    assert result.habit_name == 'Habit 2'
    assert result.periodicity == Periodicity.DAILY


def test_longest_streak_across_habits_tie_breaking():
    """Test that tie-breaking prefers lower habit_id."""
    habits = [
        HabitDTO(
            id=2,
            name='Habit 2',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
        HabitDTO(
            id=1,
            name='Habit 1',
            periodicity=Periodicity.DAILY,
            created_at=datetime.now(),
            is_active=True,
        ),
    ]
    completions = [
        # Both have streak of 2
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 1),
            period_key='2025-01-01',
        ),
        CompletionDTO(
            habit_id=1,
            completed_at=datetime(2025, 1, 2),
            period_key='2025-01-02',
        ),
        CompletionDTO(
            habit_id=2,
            completed_at=datetime(2025, 1, 5),
            period_key='2025-01-05',
        ),
        CompletionDTO(
            habit_id=2,
            completed_at=datetime(2025, 1, 6),
            period_key='2025-01-06',
        ),
    ]
    result = longest_streak_across_habits(habits, completions)
    assert result.length == 2
    assert result.habit_id == 1  # Lower ID wins in tie
    assert result.habit_name == 'Habit 1'
