from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.db import get_conn
from app.queries import follows as follows_q
from app.queries import posts as posts_q
from app.queries import users as users_q
from app.schemas.posts import PostOut
from app.schemas.users import UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    row = await users_q.get_user_by_id(conn, user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return UserPublic(**row)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await users_q.update_user(
        conn, current_user_id, payload.display_name, payload.bio, payload.is_private
    )
    return UserPublic(**row)


@router.get("/{user_id}/posts", response_model=list[PostOut])
async def get_user_posts(
    user_id: int,
    limit: int = 20,
    before: datetime | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    target = await users_q.get_user_by_id(conn, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    if target["is_private"] and user_id != current_user_id:
        allowed = await follows_q.is_accepted_follower(conn, current_user_id, user_id)
        if not allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is private")

    rows = await posts_q.list_user_posts(conn, user_id, limit, before)
    return [PostOut(**r) for r in rows]
