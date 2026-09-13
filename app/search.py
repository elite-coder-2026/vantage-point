import asyncpg

from app import avatar as avatar_svc
from app.queries import search as search_q


async def search_users(conn: asyncpg.Connection, query: str, limit: int = 20) -> list[dict]:
    rows = await search_q.search_users(conn, query, limit)
    return [{**dict(r), "avatar_path": avatar_svc.avatar_url(r["avatar_path"])} for r in rows]


async def search_hashtags(conn: asyncpg.Connection, query: str, limit: int = 20) -> list[dict]:
    rows = await search_q.search_hashtags(conn, query, limit)
    return [dict(r) for r in rows]
