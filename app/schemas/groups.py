from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class GroupCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    is_private: bool = False


class GroupOut(BaseModel):
    id: int
    owner_id: int
    name: str
    slug: str
    description: str | None
    is_private: bool
    created_at: datetime


class GroupMemberOut(BaseModel):
    user_id: int
    username: str
    role: Literal["member", "moderator", "owner"]
    joined_at: datetime


class GroupMemberAdd(BaseModel):
    user_id: int
