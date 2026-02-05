"""Pydantic DTOs for analytics operations."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from src.core.models import Periodicity


class HabitDTO(BaseModel):
    """Data transfer object for Habit."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    periodicity: Periodicity
    created_at: datetime
    is_active: bool


class CompletionDTO(BaseModel):
    """Data transfer object for Completion."""

    model_config = ConfigDict(frozen=True)

    habit_id: int
    completed_at: datetime
    period_key: str


class LongestStreakDTO(BaseModel):
    """Data transfer object for longest streak result."""

    model_config = ConfigDict(frozen=True)

    length: int
    habit_id: int | None
    habit_name: str | None
    periodicity: Periodicity | None
