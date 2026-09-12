from datetime import datetime

from pydantic import BaseModel


class ShareCreate(BaseModel):
    share_to: int


class ShareOut(BaseModel):
    id: int
    post_id: int
    share_by: int
    share_to: int
    created_at: datetime
