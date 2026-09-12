from datetime import datetime

import asyncpg


async def create_reset_token(
    conn: asyncpg.Connection, user_id: int, token_hash: str, expires_at: datetime
) -> None:
    await conn.execute(
        "INSERT INTO password_resets (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
        user_id, token_hash, expires_at,
    )


async def get_valid_reset(conn: asyncpg.Connection, token_hash: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, user_id
        FROM password_resets
        WHERE token_hash = $1 AND used_at IS NULL AND expires_at > now()
        """,
        token_hash,
    )


async def mark_used(conn: asyncpg.Connection, reset_id: int) -> None:
    await conn.execute(
        "UPDATE password_resets SET used_at = now() WHERE id = $1", reset_id
    )
