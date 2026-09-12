from datetime import datetime

from pydantic import BaseModel


class PostOut(BaseModel):
    id: int
    author_id: int
    group_id: int | None
    type: str
    body: str
    font_size: int | None
    address: str | None
    created_at: datetime

    image_path: str | None = None
    image_filter: str | None = None
    video_path: str | None = None
    audio_path: str | None = None
    document_path: str | None = None
    location_image_url: str | None = None
    link_url: str | None = None
    link_title: str | None = None
    link_image_url: str | None = None

    like_count: int = 0
    comment_count: int = 0
    share_count: int = 0
    tag_count: int = 0
    liked_by_viewer: bool = False
    bookmarked_by_viewer: bool = False


class TextPostCreate(BaseModel):
    body: str
    group_id: int | None = None
    font_size: int | None = None
    address: str | None = None
    tags: list[str] = []


class LinkPostCreate(BaseModel):
    body: str
    url: str
    title: str | None = None
    image_url: str | None = None
    group_id: int | None = None
    font_size: int | None = None
    address: str | None = None
    tags: list[str] = []


class LocationPostCreate(BaseModel):
    body: str
    image_url: str
    group_id: int | None = None
    font_size: int | None = None
    address: str | None = None
    tags: list[str] = []


class PostEdit(BaseModel):
    body: str
