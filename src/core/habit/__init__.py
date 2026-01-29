"""Habit domain module."""

from src.core.habit.errors import (
    ActiveProfileRequired,
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitError,
    HabitNotFound,
)
from src.core.habit.service import HabitService

__all__ = [
    'HabitService',
    'HabitError',
    'ActiveProfileRequired',
    'HabitNotFound',
    'HabitAlreadyExists',
    'HabitArchived',
    'HabitAlreadyCompletedForPeriod',
]
