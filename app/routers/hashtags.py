import asyncpg
from fastapi import APIRouter, Depends

from app.db import get_conn
from app.queries import hashtags as hashtags_q
from app.schemas.posts import PostOut

router = APIRouter(prefix="/hashtags", tags=["hashtags"])


@router.get("/{tag}/posts", response_model=list[PostOut])
async def get_posts_by_hashtag(tag: str, limit: int = 20, conn: asyncpg.Connection = Depends(get_conn)):
    rows = await hashtags_q.posts_by_hashtag(conn, tag, limit)
    return [PostOut(**r) for r in rows]
