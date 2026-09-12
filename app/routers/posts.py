from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.db import get_conn
from app.queries import groups as groups_q
from app.queries import hashtags as hashtags_q
from app.queries import posts as posts_q
from app.schemas.posts import PostCreate, PostOut

router = APIRouter(tags=["posts"])


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if payload.group_id is not None:
        is_member = await groups_q.is_member(conn, payload.group_id, current_user_id)
        if not is_member:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Must be a group member to post")

    async with conn.transaction():
        row = await posts_q.create_post(conn, current_user_id, payload.body, payload.group_id)
        if payload.hashtags:
            await hashtags_q.attach_hashtags(conn, row["id"], payload.hashtags)

    return PostOut(**row)


@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(post_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    row = await posts_q.get_post(conn, post_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return PostOut(**row)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    deleted = await posts_q.soft_delete_post(conn, post_id, current_user_id)
    if deleted is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


@router.get("/feed", response_model=list[PostOut])
async def get_feed(
    limit: int = 20,
    before: datetime | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await posts_q.get_feed(conn, current_user_id, limit, before)
    return [PostOut(**r) for r in rows]
