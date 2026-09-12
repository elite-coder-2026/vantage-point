import asyncpg


async def is_bookmarked(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    row = await conn.fetchrow(
        "SELECT bkmrk_id FROM bookmarks WHERE post_id = $1 AND user_id = $2",
        post_id, user_id,
    )
    return row is not None


async def create_bookmark(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await conn.execute(
        "INSERT INTO bookmarks (post_id, user_id, bookmark_time) VALUES ($1, $2, now())",
        post_id, user_id,
    )


async def delete_bookmark(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await conn.execute(
        "DELETE FROM bookmarks WHERE post_id = $1 AND user_id = $2",
        post_id, user_id,
    )
