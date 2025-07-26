import math
import time
from typing import Optional, List

from pydantic import Field

from models.user import User

from pydantic import BaseModel, StringConstraints
from typing import Annotated


class DeleteUser(BaseModel):
    username: str


class NewUser(DeleteUser):
    password: str


class LoginRequest(BaseModel):
    username: Annotated[str, StringConstraints(
        min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_.-]+$")]
    password: Annotated[str, StringConstraints(min_length=8, max_length=100)]


class UserCreateRequest(BaseModel):
    username: str
    password: str


class ProfileUpdateRequest(BaseModel):
    first_name: str = Field(..., min_length=2, max_length=50)
    last_name: str = Field(..., min_length=2, max_length=50)
    university: str = Field(..., min_length=2, max_length=100)
    year: int = Field(..., ge=1900, le=2100)  # Ensure valid year range
    speciality: str = Field(..., min_length=2, max_length=100)
    department: str = Field(..., min_length=2, max_length=100)
    degree: str = Field(..., min_length=2, max_length=100)
    role: str = Field(..., min_length=2, max_length=50)
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(
        None, min_length=5)  # Password must be >4 characters


class ProfileResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    university: str
    year: int
    role: str
    speciality: str
    department: str
    degree: str


class UserResponse(BaseModel):
    id: int
    username: str
    is_admin: bool = False
    is_active: bool = False
    has_password_reset: bool = False
    is_akg: bool = False
    group: str = Field(default="case")
    profile: Optional[ProfileResponse] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str
    is_admin: bool
    is_view: bool
    has_password_reset: bool
    is_akg: bool