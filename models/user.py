from datetime import datetime
from typing import Optional, List

from sqlmodel import Field, Relationship

from db.base import BaseSQLModel


class User(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str
    created_at: datetime = Field(default_factory=datetime.now)
    is_admin: bool = False
    is_active: bool = True
    group: str = Field(default="case")  # control
    is_akg: bool = Field(default=False, nullable=True)
    has_password_reset: bool = Field(default=False, nullable=True)
    profile: Optional["Profile"] = Relationship(back_populates="user",
                                                sa_relationship_kwargs={'lazy': 'selectin', 'uselist': False})

class Profile(BaseSQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    university: str
    year: int
    role: str
    speciality: str
    department: str
    degree: str
    user_id: Optional[int] = Field(default=None, foreign_key="user.id")
    user: Optional[User] = Relationship(back_populates="profile")
