import asyncpg


async def create_share(conn: asyncpg.Connection, post_id: int, share_by: int, share_to: int) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO post_shares (post_id, share_by, share_to)
        VALUES ($1, $2, $3)
        RETURNING id, post_id, share_by, share_to, created_at
        """,
        post_id, share_by, share_to,
    )


async def delete_share(conn: asyncpg.Connection, share_id: int, share_by: int) -> str | None:
    return await conn.fetchval(
        "DELETE FROM post_shares WHERE id = $1 AND share_by = $2 RETURNING 'ok'", share_id, share_by,
    )


async def is_shared_by(conn: asyncpg.Connection, post_id: int, share_by: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM post_shares WHERE post_id = $1 AND share_by = $2)",
        post_id, share_by,
    )


async def is_shared_to(conn: asyncpg.Connection, post_id: int, share_to: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM post_shares WHERE post_id = $1 AND share_to = $2)",
        post_id, share_to,
    )


async def count_shares(conn: asyncpg.Connection, post_id: int) -> int:
    return await conn.fetchval("SELECT COUNT(*) FROM post_shares WHERE post_id = $1", post_id)
