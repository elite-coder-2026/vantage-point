import asyncpg
from fastapi import Request

from app.config import settings


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(dsn=settings.database_url)


async def get_conn(request: Request):
    async with request.app.state.pool.acquire() as conn:
        yield conn
