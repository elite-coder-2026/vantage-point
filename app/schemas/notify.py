from datetime import datetime

from pydantic import BaseModel

from app.schemas.users import UserPublic


class NotificationOut(BaseModel):
    id: int
    type: str
    status: str
    time: datetime
    by: UserPublic | None
    of: UserPublic | None
    post_id: int | None
    comment_id: int | None
    viewer_follows_by: bool
    viewer_follows_of: bool
