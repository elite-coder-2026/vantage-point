from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class FollowRequest(BaseModel):
    followee_id: int


class FollowRespond(BaseModel):
    accept: bool


class FollowOut(BaseModel):
    id: int
    follower_id: int
    followee_id: int
    status: Literal["pending", "accepted", "rejected"]
    created_at: datetime


class FollowerOut(BaseModel):
    id: int
    username: str
    display_name: str
