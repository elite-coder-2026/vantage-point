import asyncpg


async def attach_hashtags(conn: asyncpg.Connection, post_id: int, tags: list[str]) -> None:
    for tag in tags:
        hashtag_id = await conn.fetchval(
            """
            INSERT INTO hashtags (tag) VALUES ($1)
            ON CONFLICT (tag) DO UPDATE SET tag = EXCLUDED.tag
            RETURNING id
            """,
            tag,
        )
        await conn.execute(
            """
            INSERT INTO post_hashtags (post_id, hashtag_id)
            VALUES ($1, $2)
            ON CONFLICT DO NOTHING
            """,
            post_id, hashtag_id,
        )


async def posts_by_hashtag(conn: asyncpg.Connection, tag: str, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT p.id, p.author_id, p.group_id, p.body, p.created_at
        FROM posts p
        JOIN post_hashtags ph ON ph.post_id = p.id
        JOIN hashtags h ON h.id = ph.hashtag_id
        WHERE h.tag = $1 AND p.deleted_at IS NULL
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        tag, limit,
    )
