from datetime import datetime

import asyncpg


async def create_notification(
    conn: asyncpg.Connection,
    notify_by: int,
    notify_to: int,
    type_: str,
    notify_of: int | None = None,
    post_id: int | None = None,
    comment_id: int | None = None,
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO notifications (notify_by, notify_to, notify_of, post_id, comment_id, type)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING noti_id, notify_by, notify_to, notify_of, post_id, comment_id, type, status, time
        """,
        notify_by, notify_to, notify_of, post_id, comment_id, type_,
    )


async def count_notifications(conn: asyncpg.Connection, user_id: int) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM notifications WHERE notify_to = $1", user_id
    )


async def count_unread(conn: asyncpg.Connection, user_id: int) -> int:
    return await conn.fetchval(
        "SELECT count(*) FROM notifications WHERE notify_to = $1 AND status = 'unread'", user_id
    )


async def mark_all_read(conn: asyncpg.Connection, user_id: int) -> None:
    await conn.execute(
        "UPDATE notifications SET status = 'read' WHERE notify_to = $1", user_id
    )


async def clear_notifications(conn: asyncpg.Connection, user_id: int) -> None:
    await conn.execute("DELETE FROM notifications WHERE notify_to = $1", user_id)


async def list_notifications(
    conn: asyncpg.Connection, user_id: int, before_id: int | None, limit: int
) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT noti_id, notify_by, notify_to, notify_of, post_id, comment_id, type, status, time
        FROM notifications
        WHERE notify_to = $1 AND ($3::bigint IS NULL OR noti_id < $3)
        ORDER BY noti_id DESC
        LIMIT $2
        """,
        user_id, limit, before_id,
    )
