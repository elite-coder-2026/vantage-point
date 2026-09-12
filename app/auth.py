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


async def get_current_user_id(
    request: Request, conn: asyncpg.Connection = Depends(get_conn)
) -> int:
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing bearer token")

    token = auth_header.removeprefix("Bearer ")
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    session = await sessions_q.get_active_session_by_token_hash(conn, token_hash)
    if session is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired session")

    return session["user_id"]
