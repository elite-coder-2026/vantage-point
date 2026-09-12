from datetime import datetime

from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str


class CommentOut(BaseModel):
    id: int
    post_id: int
    user_id: int
    body: str
    created_at: datetime
    like_count: int = 0
    liked_by_viewer: bool = False
