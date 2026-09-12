import asyncpg

from app.queries.posts import POST_SELECT_SQL


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


async def clear_hashtags(conn: asyncpg.Connection, post_id: int) -> None:
    await conn.execute("DELETE FROM post_hashtags WHERE post_id = $1", post_id)


async def posts_by_hashtag(
    conn: asyncpg.Connection, viewer_id: int | None, tag: str, limit: int
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        JOIN post_hashtags ph ON ph.post_id = p.id
        JOIN hashtags h ON h.id = ph.hashtag_id
        WHERE h.tag = $2
        ORDER BY p.created_at DESC
        LIMIT $3
        """,
        viewer_id, tag, limit,
    )
