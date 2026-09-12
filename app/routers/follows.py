import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user_id
from app.db import get_conn
from app.queries import follows as follows_q
from app.queries import users as users_q
from app.schemas.follows import FollowerOut, FollowOut, FollowRequest, FollowRespond


async def _ensure_visible(conn, user_id, current_user_id):
    target = await users_q.get_user_by_id(conn, user_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    if target["is_private"] and user_id != current_user_id:
        allowed = await follows_q.is_accepted_follower(conn, current_user_id, user_id)
        if not allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "This account is private")

router = APIRouter(tags=["follows"])


@router.post("/follows", response_model=FollowOut, status_code=status.HTTP_201_CREATED)
async def create_follow(
    payload: FollowRequest,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if payload.followee_id == current_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot follow yourself")

    target = await users_q.get_user_by_id(conn, payload.followee_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")

    row = await follows_q.create_follow(conn, current_user_id, payload.followee_id, target["is_private"])
    return FollowOut(**row)


@router.post("/follows/{follow_id}/respond", response_model=FollowOut)
async def respond_to_follow(
    follow_id: int,
    payload: FollowRespond,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await follows_q.respond_to_follow(conn, follow_id, current_user_id, payload.accept)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pending follow request not found")
    return FollowOut(**row)


@router.delete("/follows/{follow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_follow(
    follow_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    deleted = await follows_q.delete_follow(conn, follow_id, current_user_id)
    if deleted is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Follow not found")


@router.get("/users/{user_id}/followers", response_model=list[FollowerOut])
async def list_followers(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _ensure_visible(conn, user_id, current_user_id)
    rows = await follows_q.list_followers(conn, user_id)
    return [FollowerOut(**r) for r in rows]


@router.get("/users/{user_id}/following", response_model=list[FollowerOut])
async def list_following(
    user_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _ensure_visible(conn, user_id, current_user_id)
    rows = await follows_q.list_following(conn, user_id)
    return [FollowerOut(**r) for r in rows]
