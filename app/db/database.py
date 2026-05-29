from collections.abc import AsyncIterator

import asyncpg

from app.core.config import get_settings

_pool: asyncpg.Pool | None = None


async def init_db_pool() -> None:
    global _pool
    settings = get_settings()
    ssl = 'require' if settings.database_ssl else None
    _pool = await asyncpg.create_pool(settings.database_url, min_size=1, max_size=10, ssl=ssl)


async def close_db_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def get_db() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        await init_db_pool()
    assert _pool is not None
    async with _pool.acquire() as conn:
        yield conn
