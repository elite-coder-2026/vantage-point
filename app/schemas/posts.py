from datetime import datetime

from pydantic import BaseModel


class PostCreate(BaseModel):
    body: str
    group_id: int | None = None
    hashtags: list[str] = []


class PostOut(BaseModel):
    id: int
    author_id: int
    group_id: int | None
    body: str
    created_at: datetime
