import asyncpg


async def create_follow(
    conn: asyncpg.Connection, follower_id: int, followee_id: int, target_is_private: bool
) -> asyncpg.Record:
    status = "pending" if target_is_private else "accepted"
    return await conn.fetchrow(
        """
        INSERT INTO follows (follower_id, followee_id, status)
        VALUES ($1, $2, $3)
        ON CONFLICT (follower_id, followee_id) DO UPDATE
            SET status = CASE WHEN follows.status = 'rejected' THEN EXCLUDED.status ELSE follows.status END
        RETURNING id, follower_id, followee_id, status, created_at
        """,
        follower_id, followee_id, status,
    )


async def respond_to_follow(
    conn: asyncpg.Connection, follow_id: int, followee_id: int, accept: bool
) -> asyncpg.Record | None:
    status = "accepted" if accept else "rejected"
    return await conn.fetchrow(
        """
        UPDATE follows
        SET status = $1, responded_at = now()
        WHERE id = $2 AND followee_id = $3 AND status = 'pending'
        RETURNING id, follower_id, followee_id, status, created_at
        """,
        status, follow_id, followee_id,
    )


async def delete_follow(conn: asyncpg.Connection, follow_id: int, follower_id: int) -> str | None:
    return await conn.fetchval(
        "DELETE FROM follows WHERE id = $1 AND follower_id = $2 RETURNING 'ok'",
        follow_id, follower_id,
    )


async def delete_follow_by_pair(conn: asyncpg.Connection, follower_id: int, followee_id: int) -> None:
    await conn.execute(
        "DELETE FROM follows WHERE follower_id = $1 AND followee_id = $2",
        follower_id, followee_id,
    )


async def get_follow_status(conn: asyncpg.Connection, follower_id: int, followee_id: int) -> str | None:
    return await conn.fetchval(
        "SELECT status FROM follows WHERE follower_id = $1 AND followee_id = $2",
        follower_id, followee_id,
    )


async def list_followers(conn: asyncpg.Connection, user_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT u.id, u.username, u.display_name
        FROM follows f JOIN users u ON u.id = f.follower_id
        WHERE f.followee_id = $1 AND f.status = 'accepted'
        ORDER BY f.created_at DESC
        """,
        user_id,
    )


async def list_following(conn: asyncpg.Connection, user_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT u.id, u.username, u.display_name
        FROM follows f JOIN users u ON u.id = f.followee_id
        WHERE f.follower_id = $1 AND f.status = 'accepted'
        ORDER BY f.created_at DESC
        """,
        user_id,
    )


async def is_accepted_follower(conn: asyncpg.Connection, follower_id: int, followee_id: int) -> bool:
    return await conn.fetchval(
        """
        SELECT EXISTS (
            SELECT 1 FROM follows
            WHERE follower_id = $1 AND followee_id = $2 AND status = 'accepted'
        )
        """,
        follower_id, followee_id,
    )


async def count_followers(conn: asyncpg.Connection, user_id: int) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM follows WHERE followee_id = $1 AND status = 'accepted'", user_id
    )


async def count_following(conn: asyncpg.Connection, user_id: int) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM follows WHERE follower_id = $1 AND status = 'accepted'", user_id
    )


async def paginated_followers(
    conn: asyncpg.Connection, followee_id: int, way: str, limit: int, page_size: int
) -> list[asyncpg.Record]:
    if way == "ajax":
        return await conn.fetch(
            """
            SELECT f.id, f.follower_id, u.username, f.created_at
            FROM follows f JOIN users u ON u.id = f.follower_id
            WHERE f.followee_id = $1 AND f.status = 'accepted' AND f.id < $2
            ORDER BY f.id DESC
            LIMIT $3
            """,
            followee_id, limit, page_size,
        )
    return await conn.fetch(
        """
        SELECT f.id, f.follower_id, u.username, f.created_at
        FROM follows f JOIN users u ON u.id = f.follower_id
        WHERE f.followee_id = $1 AND f.status = 'accepted'
        ORDER BY f.id DESC
        LIMIT $2
        """,
        followee_id, limit,
    )


async def paginated_following(
    conn: asyncpg.Connection, follower_id: int, way: str, limit: int, page_size: int
) -> list[asyncpg.Record]:
    if way == "ajax":
        return await conn.fetch(
            """
            SELECT f.id, f.followee_id, u.username, f.created_at
            FROM follows f JOIN users u ON u.id = f.followee_id
            WHERE f.follower_id = $1 AND f.status = 'accepted' AND f.id < $2
            ORDER BY f.id DESC
            LIMIT $3
            """,
            follower_id, limit, page_size,
        )
    return await conn.fetch(
        """
        SELECT f.id, f.followee_id, u.username, f.created_at
        FROM follows f JOIN users u ON u.id = f.followee_id
        WHERE f.follower_id = $1 AND f.status = 'accepted'
        ORDER BY f.id DESC
        LIMIT $2
        """,
        follower_id, limit,
    )


# ---------------------------------------------------------------------------
# Profile-view tracking (backed by the separate `profile_views` table).
# Not "follow" state, kept as-is — not part of the follow_system consolidation.
# ---------------------------------------------------------------------------


async def insert_profile_view(conn: asyncpg.Connection, view_from: int, view_to: int) -> None:
    await conn.execute(
        "INSERT INTO profile_views (view_from, view_to) VALUES ($1, $2)",
        view_from, view_to,
    )


async def count_profile_viewers(conn: asyncpg.Connection, user_id: int) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM profile_views WHERE view_to = $1", user_id
    )


async def list_profile_viewers(conn: asyncpg.Connection, user_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT v.view_from, u.username
        FROM profile_views v JOIN users u ON u.id = v.view_from
        WHERE v.view_to = $1
        ORDER BY v.view_id DESC
        """,
        user_id,
    )
