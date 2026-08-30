from datetime import datetime
from enum import StrEnum

from sqlmodel import Field, SQLModel, UniqueConstraint


class Periodicity(StrEnum):
    """Habit periodicity types."""

    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'


class AfterAction(StrEnum):
    """What interactive home does after a selected action."""

    HOME = 'home'
    EXIT = 'exit'


def require_persisted_id(record_id: int | None, record_name: str) -> int:
    """Return an ORM record ID or fail clearly if the record is not persisted."""
    if record_id is None:
        raise RuntimeError(f'{record_name} has not been persisted')
    return record_id


class Profile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)
    after_action: AfterAction = Field(default=AfterAction.HOME)


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
    icon: str | None = Field(default=None)


class Completion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    habit_id: int = Field(foreign_key='habit.id', index=True)
    completed_at: datetime = Field(default_factory=datetime.now)
    period_key: str

    __table_args__ = (
        UniqueConstraint('habit_id', 'period_key', name='unique_habit_period'),
    )


class XPEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    profile_id: int = Field(foreign_key='profile.id', index=True)
    amount: int = Field(gt=0)
    reason: str
    awarded_at: datetime = Field(default_factory=datetime.now)
    habit_id: int | None = Field(default=None, foreign_key='habit.id', index=True)
    completion_id: int | None = Field(
        default=None, foreign_key='completion.id', unique=True
    )
