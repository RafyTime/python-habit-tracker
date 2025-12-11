from datetime import datetime

from sqlmodel import Field, SQLModel


class Profile(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.now)


class ActiveSession(SQLModel, table=True):
    id: int = Field(default=1, primary_key=True)
    active_profile_id: int | None = Field(default=None, foreign_key='profile.id')
