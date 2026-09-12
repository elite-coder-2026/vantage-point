from datetime import datetime

import asyncpg


async def create_post(
    conn: asyncpg.Connection, author_id: int, body: str, group_id: int | None
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO posts (author_id, group_id, body)
        VALUES ($1, $2, $3)
        RETURNING id, author_id, group_id, body, created_at
        """,
        author_id, group_id, body,
    )


async def get_post(conn: asyncpg.Connection, post_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, author_id, group_id, body, created_at
        FROM posts WHERE id = $1 AND deleted_at IS NULL
        """,
        post_id,
    )


async def soft_delete_post(conn: asyncpg.Connection, post_id: int, author_id: int) -> str | None:
    return await conn.fetchval(
        """
        UPDATE posts SET deleted_at = now()
        WHERE id = $1 AND author_id = $2 AND deleted_at IS NULL
        RETURNING 'ok'
        """,
        post_id, author_id,
    )


async def get_feed(
    conn: asyncpg.Connection, viewer_id: int, limit: int, before: datetime | None
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT p.id, p.author_id, p.group_id, p.body, p.created_at
        FROM posts p
        WHERE p.deleted_at IS NULL
          AND p.group_id IS NULL
          AND (
            p.author_id = $1
            OR p.author_id IN (
                SELECT followee_id FROM follows
                WHERE follower_id = $1 AND status = 'accepted'
            )
          )
          AND ($3::timestamptz IS NULL OR p.created_at < $3)
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        viewer_id, limit, before,
    )


async def list_user_posts(
    conn: asyncpg.Connection, author_id: int, limit: int, before: datetime | None
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT id, author_id, group_id, body, created_at
        FROM posts
        WHERE author_id = $1 AND deleted_at IS NULL
          AND ($3::timestamptz IS NULL OR created_at < $3)
        ORDER BY created_at DESC
        LIMIT $2
        """,
        author_id, limit, before,
    )
