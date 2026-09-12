import asyncpg
from fastapi import APIRouter, Depends, HTTPException, status

from app import settings as settings_svc
from app.auth import get_current_user_id
from app.db import get_conn
from app.schemas.settings import (
    AccountTypeOut,
    BlockActionOut,
    BlockedUserOut,
    ChangeAccountTypeRequest,
    ChangePasswordRequest,
    ChangePasswordResult,
    LoginHistoryOut,
    PrivacyOut,
    PrivacyRequest,
)

router = APIRouter(prefix="/settings", tags=["settings"])


@router.post("/password", response_model=ChangePasswordResult)
async def change_password(
    payload: ChangePasswordRequest,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    message = await settings_svc.change_password(
        conn, user_id, payload.current_password, payload.new_password, payload.confirm_new_password
    )
    if message == "Incorrect password":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, message)
    if message == "New passwords don't match":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, message)
    return ChangePasswordResult(message=message)


@router.put("/account-type", response_model=AccountTypeOut)
async def change_account_type(
    payload: ChangeAccountTypeRequest,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    value = await settings_svc.change_account_type(conn, user_id, payload.value)
    return AccountTypeOut(type=value)


@router.post("/block/{target_id}", response_model=BlockActionOut)
async def block_user(
    target_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if target_id == user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot block yourself")

    username = await settings_svc.block(conn, user_id, target_id)
    if username is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "User is already blocked")
    return BlockActionOut(username=username)


@router.delete("/block/{target_id}", response_model=BlockActionOut)
async def unblock_user(
    target_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    username = await settings_svc.unblock(conn, user_id, target_id)
    if username is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User is not blocked")
    return BlockActionOut(username=username)


@router.get("/block/{target_id}/status")
async def block_status(
    target_id: int,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return {
        "is_blocked": await settings_svc.is_blocked(conn, user_id, target_id),
        "am_i_blocked": await settings_svc.am_i_blocked(conn, user_id, target_id),
    }


@router.get("/blocked", response_model=list[BlockedUserOut])
async def blocked_users(
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await settings_svc.blocked_users(conn, user_id)


@router.get("/privacy/email", response_model=PrivacyOut)
async def get_email_privacy(
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return PrivacyOut(options=await settings_svc.email_privacy(conn, user_id))


@router.put("/privacy/email", response_model=PrivacyOut)
async def put_email_privacy(
    payload: PrivacyRequest,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    try:
        await settings_svc.change_email_privacy(conn, user_id, payload.value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PrivacyOut(options=await settings_svc.email_privacy(conn, user_id))


@router.get("/privacy/mobile", response_model=PrivacyOut)
async def get_mobile_privacy(
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return PrivacyOut(options=await settings_svc.mobile_privacy(conn, user_id))


@router.put("/privacy/mobile", response_model=PrivacyOut)
async def put_mobile_privacy(
    payload: PrivacyRequest,
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    try:
        await settings_svc.change_mobile_privacy(conn, user_id, payload.value)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PrivacyOut(options=await settings_svc.mobile_privacy(conn, user_id))


@router.get("/login-history", response_model=list[LoginHistoryOut])
async def login_history(
    user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    return await settings_svc.login_details(conn, user_id)
