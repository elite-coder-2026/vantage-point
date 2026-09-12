import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import asyncpg
from fastapi import Depends, HTTPException, Request, status
from passlib.context import CryptContext

from app.config import settings
from app.db import get_conn
from app.queries import sessions as sessions_q

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def generate_session_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def session_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.session_ttl_seconds)


SESSION_COOKIE_NAME = "vp_session"


def _extract_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.removeprefix("Bearer ")
    return request.cookies.get(SESSION_COOKIE_NAME)


async def get_current_user_id(
    request: Request, conn: asyncpg.Connection = Depends(get_conn)
) -> int:
    token = _extract_token(request)
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing session token")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = await sessions_q.get_active_session_by_token_hash(conn, token_hash)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")

    return session["user_id"]


async def get_current_user_id_optional(
    request: Request, conn: asyncpg.Connection = Depends(get_conn)
) -> int | None:
    token = _extract_token(request)
    if token is None:
        return None

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    session = await sessions_q.get_active_session_by_token_hash(conn, token_hash)
    return session["user_id"] if session else None
