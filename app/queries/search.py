import asyncpg


async def search_users(conn: asyncpg.Connection, query: str, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT id, username, display_name, bio, is_private, avatar_path, created_at
        FROM users
        WHERE username ILIKE $1 OR display_name ILIKE $1
        ORDER BY username
        LIMIT $2
        """,
        f"%{query}%", limit,
    )


async def search_hashtags(conn: asyncpg.Connection, query: str, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        "SELECT id, tag FROM hashtags WHERE tag ILIKE $1 ORDER BY tag LIMIT $2",
        f"%{query}%", limit,
    )
