import asyncpg


async def create_group(
    conn: asyncpg.Connection, owner_id: int, name: str, slug: str, description: str | None, is_private: bool
) -> asyncpg.Record:
    async with conn.transaction():
        group = await conn.fetchrow(
            """
            INSERT INTO groups (owner_id, name, slug, description, is_private)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, owner_id, name, slug, description, is_private, created_at
            """,
            owner_id, name, slug, description, is_private,
        )
        await conn.execute(
            """
            INSERT INTO group_members (group_id, user_id, role)
            VALUES ($1, $2, 'owner')
            """,
            group["id"], owner_id,
        )
    return group


async def get_group_by_id(conn: asyncpg.Connection, group_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        SELECT id, owner_id, name, slug, description, is_private, created_at
        FROM groups WHERE id = $1
        """,
        group_id,
    )


async def add_member(conn: asyncpg.Connection, group_id: int, user_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(
        """
        WITH inserted AS (
            INSERT INTO group_members (group_id, user_id, role)
            VALUES ($1, $2, 'member')
            ON CONFLICT (group_id, user_id) DO NOTHING
            RETURNING group_id, user_id, role, joined_at
        )
        SELECT i.user_id, u.username, i.role, i.joined_at
        FROM inserted i JOIN users u ON u.id = i.user_id
        """,
        group_id, user_id,
    )


async def remove_member(conn: asyncpg.Connection, group_id: int, user_id: int) -> str | None:
    return await conn.fetchval(
        "DELETE FROM group_members WHERE group_id = $1 AND user_id = $2 RETURNING 'ok'",
        group_id, user_id,
    )


async def is_member(conn: asyncpg.Connection, group_id: int, user_id: int) -> bool:
    return await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM group_members WHERE group_id = $1 AND user_id = $2)",
        group_id, user_id,
    )


async def list_members(conn: asyncpg.Connection, group_id: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT gm.user_id, u.username, gm.role, gm.joined_at
        FROM group_members gm JOIN users u ON u.id = gm.user_id
        WHERE gm.group_id = $1
        ORDER BY gm.joined_at
        """,
        group_id,
    )
