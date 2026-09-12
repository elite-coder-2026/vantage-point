from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app import avatar as avatar_svc
from app import posts as posts_svc
from app.auth import get_current_user_id
from app.db import get_conn
from app.queries import follows as follows_q
from app.queries import users as users_q
from app.schemas.posts import PostOut
from app.schemas.users import UserPublic, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _to_public(row: asyncpg.Record) -> UserPublic:
    return UserPublic(**{**row, "avatar_path": avatar_svc.avatar_url(row["avatar_path"])})


@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, conn: asyncpg.Connection = Depends(get_conn)):
    row = await users_q.get_user_by_id(conn, user_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return _to_public(row)


@router.patch("/me", response_model=UserPublic)
async def update_me(
    payload: UserUpdate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await users_q.update_user(
        conn, current_user_id, payload.display_name, payload.bio, payload.is_private
    )
    return _to_public(row)


@router.post("/me/avatar", response_model=UserPublic)
async def upload_avatar(
    file: UploadFile,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    content = await file.read()
    try:
        data = await avatar_svc.upload_avatar(conn, current_user_id, content, file.filename or "")
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return UserPublic(**data)


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

    rows = await posts_svc.list_user_posts(conn, current_user_id, user_id, limit, before)
    return [PostOut(**r) for r in rows]


async def _check_visible(conn: asyncpg.Connection, user_id: int, current_user_id: int) -> None:
    target = await users_q.get_user_by_id(conn, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target["is_private"] and user_id != current_user_id:
        allowed = await follows_q.is_accepted_follower(conn, current_user_id, user_id)
        if not allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is private")


@router.get("/{user_id}/tagged-posts", response_model=list[PostOut])
async def get_tagged_posts(
    user_id: int,
    limit: int = 20,
    before_id: int | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _check_visible(conn, user_id, current_user_id)
    rows = await posts_svc.list_tagged(conn, current_user_id, user_id, limit, before_id)
    return [PostOut(**r) for r in rows]


@router.get("/{user_id}/photos", response_model=list[dict])
async def get_photos(
    user_id: int,
    limit: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _check_visible(conn, user_id, current_user_id)
    return await posts_svc.list_photos(conn, user_id, limit)


@router.get("/{user_id}/videos", response_model=list[dict])
async def get_videos(
    user_id: int,
    limit: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _check_visible(conn, user_id, current_user_id)
    return await posts_svc.list_videos(conn, user_id, limit)


@router.get("/{user_id}/audios", response_model=list[dict])
async def get_audios(
    user_id: int,
    limit: int = 20,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _check_visible(conn, user_id, current_user_id)
    return await posts_svc.list_audios(conn, user_id, limit)
