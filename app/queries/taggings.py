import asyncpg


async def tag_users(conn: asyncpg.Connection, post_id: int, user_ids: list[int]) -> None:
    for user_id in user_ids:
        await conn.execute(
            "INSERT INTO post_taggings (post_id, tagged_user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            post_id, user_id,
        )


async def untag_user(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await conn.execute(
        "DELETE FROM post_taggings WHERE post_id = $1 AND tagged_user_id = $2", post_id, user_id,
    )


async def am_i_tagged(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM post_taggings WHERE post_id = $1 AND tagged_user_id = $2)",
        post_id, user_id,
    )


async def list_taggings(conn: asyncpg.Connection, post_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT u.id, u.username
        FROM post_taggings pt JOIN users u ON u.id = pt.tagged_user_id
        WHERE pt.post_id = $1
        ORDER BY pt.id
        """,
        post_id,
    )


async def count_taggings(conn: asyncpg.Connection, post_id: int) -> int:
    return await conn.fetchval("SELECT COUNT(*) FROM post_taggings WHERE post_id = $1", post_id)
