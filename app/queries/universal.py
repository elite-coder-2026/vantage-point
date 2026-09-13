import asyncpg


async def get_username_by_id(conn: asyncpg.Connection, user_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT username FROM users WHERE id = $1", user_id)


async def get_id_by_username(conn: asyncpg.Connection, username: str) -> asyncpg.Record | None:
    return await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)


async def get_user_detail(conn: asyncpg.Connection, user_id: int, what: str) -> asyncpg.Record | None:
    return await conn.fetchrow(f"SELECT {what} FROM users WHERE id = $1", user_id)
