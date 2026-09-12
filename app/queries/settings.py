import asyncpg


async def insert_default_privacy(conn: asyncpg.Connection, user_id: int) -> None:
    await conn.execute(
        "INSERT INTO email_private (user_id, options) VALUES ($1, 'public')", user_id
    )
    await conn.execute(
        "INSERT INTO mobile_private (user_id, options) VALUES ($1, 'public')", user_id
    )


async def get_password_hash(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await conn.fetchval(
        "SELECT password_hash FROM users WHERE id = $1", user_id
    )


async def update_password(conn: asyncpg.Connection, user_id: int, password_hash: str) -> None:
    await conn.execute(
        "UPDATE users SET password_hash = $2, updated_at = now() WHERE id = $1",
        user_id, password_hash,
    )


async def update_account_type(conn: asyncpg.Connection, user_id: int, value: str) -> None:
    await conn.execute(
        "UPDATE users SET type = $2, updated_at = now() WHERE id = $1", user_id, value
    )


async def get_account_type(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await conn.fetchval("SELECT type FROM users WHERE id = $1", user_id)


async def create_block(conn: asyncpg.Connection, block_by: int, block_to: int) -> None:
    await conn.execute(
        "INSERT INTO block (block_by, block_to, time) VALUES ($1, $2, now())",
        block_by, block_to,
    )


async def delete_block(conn: asyncpg.Connection, block_by: int, block_to: int) -> str | None:
    return await conn.fetchval(
        "DELETE FROM block WHERE block_by = $1 AND block_to = $2 RETURNING 'ok'",
        block_by, block_to,
    )


async def is_blocked(conn: asyncpg.Connection, block_by: int, block_to: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM block WHERE block_by = $1 AND block_to = $2)",
        block_by, block_to,
    )


async def list_blocked_users(conn: asyncpg.Connection, block_by: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT u.id, u.username, u.display_name, b.time
        FROM block b JOIN users u ON u.id = b.block_to
        WHERE b.block_by = $1
        ORDER BY b.time DESC
        """,
        block_by,
    )


async def get_email_privacy(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await conn.fetchval(
        "SELECT options FROM email_private WHERE user_id = $1", user_id
    )


async def get_mobile_privacy(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await conn.fetchval(
        "SELECT options FROM mobile_private WHERE user_id = $1", user_id
    )


async def update_email_privacy(conn: asyncpg.Connection, user_id: int, value: str) -> None:
    await conn.execute(
        "UPDATE email_private SET options = $2 WHERE user_id = $1", user_id, value
    )


async def update_mobile_privacy(conn: asyncpg.Connection, user_id: int, value: str) -> None:
    await conn.execute(
        "UPDATE mobile_private SET options = $2 WHERE user_id = $1", user_id, value
    )


async def list_login_history(conn: asyncpg.Connection, user_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT time, os, browser, ip, logout_time
        FROM login_history
        WHERE user_id = $1
        ORDER BY time DESC
        """,
        user_id,
    )
