from datetime import datetime

from sqlmodel import SQLModel, Field


class BaseSQLModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
