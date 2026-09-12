from datetime import datetime

import asyncpg


async def create_session(
    conn: asyncpg.Connection,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
    user_agent: str | None,
    ip_address: str | None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO sessions (user_id, token_hash, expires_at, user_agent, ip_address)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING id, user_id, expires_at
        """,
        user_id, token_hash, expires_at, user_agent, ip_address,
    )


async def get_active_session_by_token_hash(conn: asyncpg.Connection, token_hash: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, user_id, expires_at
        FROM sessions
        WHERE token_hash = $1 AND revoked_at IS NULL AND expires_at > now()
        """,
        token_hash,
    )


async def revoke_session(conn: asyncpg.Connection, token_hash: str) -> None:
    await conn.execute(
        "UPDATE sessions SET revoked_at = now() WHERE token_hash = $1",
        token_hash,
    )
