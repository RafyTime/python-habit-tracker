from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel, UniqueConstraint


class Periodicity(str, Enum):
    """Habit periodicity types."""

    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


class Profile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class AppState(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    active_profile_id: int | None = Field(default=None, foreign_key='profile.id')


class Habit(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key='profile.id', index=True)
    name: str
    periodicity: Periodicity
    created_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = Field(default=True, index=True)


class Completion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key='habit.id', index=True)
    completed_at: datetime = Field(default_factory=datetime.now)
    period_key: str

    __table_args__ = (
        UniqueConstraint('habit_id', 'period_key', name='unique_habit_period'),
    )
