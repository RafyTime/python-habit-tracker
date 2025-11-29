from datetime import datetime

from sqlmodel import Field, SQLModel


class Item(SQLModel, table=True):
    """Item model for the habit tracker"""

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
