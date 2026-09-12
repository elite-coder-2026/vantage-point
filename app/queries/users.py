import asyncpg


async def create_user(
    conn: asyncpg.Connection, username: str, email: str, password_hash: str, display_name: str
) -> asyncpg.Record:
    return await conn.fetchrow(
        """
        INSERT INTO users (username, email, password_hash, display_name)
        VALUES ($1, $2, $3, $4)
        RETURNING id, username, display_name, bio, is_private, created_at
        """,
        username, email, password_hash, display_name,
    )


async def get_user_by_id(conn: asyncpg.Connection, user_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, username, display_name, bio, is_private, created_at
        FROM users WHERE id = $1
        """,
        user_id,
    )


async def get_user_by_username_with_auth(conn: asyncpg.Connection, username: str) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, username, email, password_hash, display_name, bio, is_private, created_at
        FROM users WHERE username = $1
        """,
        username,
    )


async def update_user(
    conn: asyncpg.Connection,
    user_id: int,
    display_name: str | None,
    bio: str | None,
    is_private: bool | None,
) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        UPDATE users
        SET display_name = COALESCE($2, display_name),
            bio = COALESCE($3, bio),
            is_private = COALESCE($4, is_private),
            updated_at = now()
        WHERE id = $1
        RETURNING id, username, display_name, bio, is_private, created_at
        """,
        user_id, display_name, bio, is_private,
    )
