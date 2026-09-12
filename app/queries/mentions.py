import asyncpg


async def create_mentions(conn: asyncpg.Connection, post_id: int, user_ids: list[int]) -> None:
    for user_id in user_ids:
        await conn.execute(
            "INSERT INTO post_mentions (post_id, mentioned_user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            post_id, user_id,
        )


async def clear_mentions(conn: asyncpg.Connection, post_id: int) -> None:
    await conn.execute("DELETE FROM post_mentions WHERE post_id = $1", post_id)


async def list_mentions(conn: asyncpg.Connection, post_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT u.id, u.username
        FROM post_mentions pm JOIN users u ON u.id = pm.mentioned_user_id
        WHERE pm.post_id = $1
        """,
        post_id,
    )
