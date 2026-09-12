import asyncpg


async def create_comment(conn: asyncpg.Connection, post_id: int, user_id: int, body: str) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO post_comments (post_id, user_id, body)
        VALUES ($1, $2, $3)
        RETURNING id, post_id, user_id, body, created_at
        """,
        post_id, user_id, body,
    )


async def get_comment(conn: asyncpg.Connection, comment_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(
        "SELECT id, post_id, user_id, body, created_at FROM post_comments WHERE id = $1 AND deleted_at IS NULL",
        comment_id,
    )


async def delete_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> str | None:
    return await conn.fetchval(
        """
        UPDATE post_comments SET deleted_at = now()
        WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL
        RETURNING 'ok'
        """,
        comment_id, user_id,
    )


async def list_comments(
    conn: asyncpg.Connection, viewer_id: int | None, post_id: int, limit: int, before_id: int | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT c.id, c.post_id, c.user_id, c.body, c.created_at,
            (SELECT COUNT(*) FROM comment_likes WHERE comment_id = c.id) AS like_count,
            EXISTS(SELECT 1 FROM comment_likes WHERE comment_id = c.id AND user_id = $1) AS liked_by_viewer
        FROM post_comments c
        WHERE c.post_id = $2 AND c.deleted_at IS NULL
          AND ($4::bigint IS NULL OR c.id < $4)
        ORDER BY c.id DESC
        LIMIT $3
        """,
        viewer_id, post_id, limit, before_id,
    )


async def count_comments(conn: asyncpg.Connection, post_id: int) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM post_comments WHERE post_id = $1 AND deleted_at IS NULL", post_id,
    )
