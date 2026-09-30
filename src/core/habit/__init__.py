"""Habit domain module."""

from src.core.habit.errors import (
    HabitAlreadyCompletedForPeriod,
    HabitAlreadyExists,
    HabitArchived,
    HabitArchivedNameExists,
    HabitError,
    HabitNotFound,
)
from src.core.habit.service import HabitService

__all__ = [
    'HabitService',
    'HabitError',
    'HabitNotFound',
    'HabitAlreadyExists',
    'HabitArchivedNameExists',
    'HabitArchived',
    'HabitAlreadyCompletedForPeriod',
]
