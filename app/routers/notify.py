import asyncpg
from fastapi import APIRouter, Depends, status

from app import avatar as avatar_svc
from app import notify as notify_svc
from app.auth import get_current_user_id
from app.db import get_conn
from app.schemas.notify import NotificationOut

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _fix_avatar(user: dict | None) -> dict | None:
    if user is None:
        return None
    return {**user, "avatar_path": avatar_svc.avatar_url(user["avatar_path"])}


@router.get("/list", response_model=list[NotificationOut])
async def get_notifications(
    before_id: int | None = None,
    limit: int = 10,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    notifications = await notify_svc.get_notifications(conn, current_user_id, before_id, limit)
    for n in notifications:
        n["by"] = _fix_avatar(n["by"])
        n["of"] = _fix_avatar(n["of"])
    return [NotificationOut(**n) for n in notifications]


@router.get("/unread-count")
async def get_unread_badge(
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return {"badge": await notify_svc.title_noti(conn, current_user_id)}


@router.post("/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await notify_svc.mark_read(conn, current_user_id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_notifications(
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await notify_svc.clear_notifications(conn, current_user_id)
