from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    display_name: str


class UserPublic(BaseModel):
    id: int
    username: str
    display_name: str
    bio: str | None
    is_private: bool
    avatar_path: str | None = None
    created_at: datetime


class UserUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    is_private: bool | None = None
