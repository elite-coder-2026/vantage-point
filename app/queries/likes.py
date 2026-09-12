import asyncpg


async def like_post(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await conn.execute(
        "INSERT INTO post_likes (post_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        post_id, user_id,
    )


async def unlike_post(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await conn.execute(
        "DELETE FROM post_likes WHERE post_id = $1 AND user_id = $2", post_id, user_id,
    )


async def is_post_liked(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM post_likes WHERE post_id = $1 AND user_id = $2)",
        post_id, user_id,
    )


async def count_post_likes(conn: asyncpg.Connection, post_id: int) -> int:
    return await conn.fetchval("SELECT COUNT(*) FROM post_likes WHERE post_id = $1", post_id)


async def like_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> None:
    await conn.execute(
        "INSERT INTO comment_likes (comment_id, user_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
        comment_id, user_id,
    )


async def unlike_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> None:
    await conn.execute(
        "DELETE FROM comment_likes WHERE comment_id = $1 AND user_id = $2", comment_id, user_id,
    )


async def is_comment_liked(conn: asyncpg.Connection, comment_id: int, user_id: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM comment_likes WHERE comment_id = $1 AND user_id = $2)",
        comment_id, user_id,
    )


async def count_comment_likes(conn: asyncpg.Connection, comment_id: int) -> int:
    return await conn.fetchval("SELECT COUNT(*) FROM comment_likes WHERE comment_id = $1", comment_id)
