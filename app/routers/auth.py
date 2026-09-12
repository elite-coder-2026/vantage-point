import hashlib

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app import avatar as avatar_svc
from app.auth import (
    generate_session_token,
    get_current_user_id,
    hash_password,
    session_expiry,
    verify_password,
)
from app.db import get_conn
from app.queries import sessions as sessions_q
from app.queries import users as users_q
from app.schemas.auth import LoginRequest, SessionOut
from app.schemas.users import UserCreate, UserPublic

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, conn: asyncpg.Connection = Depends(get_conn)):
    existing = await users_q.get_user_by_username_with_auth(conn, payload.username)
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")

    row = await users_q.create_user(
        conn, payload.username, payload.email, hash_password(payload.password), payload.display_name
    )
    return UserPublic(**{**row, "avatar_path": avatar_svc.avatar_url(row["avatar_path"])})


@router.post("/login", response_model=SessionOut)
async def login(
    payload: LoginRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await users_q.get_user_by_username_with_auth(conn, payload.username)
    if row is None or not verify_password(payload.password, row["password_hash"]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

    token, token_hash = generate_session_token()
    ip_address = request.client.host if request.client else None
    await sessions_q.create_session(conn, row["id"], token_hash, session_expiry(), user_agent, ip_address)

    return SessionOut(
        token=token,
        user=UserPublic(
            id=row["id"],
            username=row["username"],
            display_name=row["display_name"],
            bio=row["bio"],
            is_private=row["is_private"],
            avatar_path=avatar_svc.avatar_url(row["avatar_path"]),
            created_at=row["created_at"],
        ),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    authorization: str = Header(...),
    _user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    token = authorization.removeprefix("Bearer ")
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    await sessions_q.revoke_session(conn, token_hash)
